import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List

from celery.schedules import crontab

from app.core.settings import settings
from app.db.session import SessionLocal
from app.db.models import Node, Edge
from app.repositories.edges_repo import EdgesRepository
from app.repositories.nodes_repo import NodesRepository
from app.workers.celery_app import celery
from app.wiki.client import fetch_outbound_titles
from app.core.redis_client import redis_client
from app.repositories.edges_repo import EdgesRepository

logger = logging.getLogger(__name__)

_valid_names_cache: set[str] | None = None


def _load_valid_names() -> set[str]:
    """Load valid names from seed file (only these will be used for edges)."""
    global _valid_names_cache
    if _valid_names_cache is not None:
        return _valid_names_cache

    path = Path(settings.seed_file_path)
    valid_names = set()

    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    valid_names.add(name)

    _valid_names_cache = valid_names
    return valid_names


async def _sync_batch_once(batch_size: int = 100) -> tuple[int, int]:
    """
    One incremental sync pass: pick a batch of nodes and refresh their outbound links.
    Returns: (nodes_processed, edges_added)
    """
    async with SessionLocal() as session:
        nodes_repo = NodesRepository(session)
        edges_repo = EdgesRepository(session)

        nodes = await nodes_repo.get_batch_for_sync(limit=batch_size)
        if not nodes:
            return (0, 0)

        valid_names = _load_valid_names()

        total_edges_added = 0
        for node in nodes:
            node_edges = 0
            try:
                titles = fetch_outbound_titles(node.title)
            except Exception as exc:  
                logger.error("Failed to fetch links for %s: %s", node.title, exc, exc_info=True)
                continue

            for title in titles:
                if title not in valid_names:
                    continue

                linked = await nodes_repo.get_by_title(title)
                if linked is None:
                    continue

                inserted = await edges_repo.add_edge(node.id, linked.id)
                if inserted:
                    total_edges_added += 1
                    node_edges += 1

        await session.commit()
        return (len(nodes), total_edges_added)


@celery.task(name="sync_wiki_incremental")
def sync_wiki_incremental() -> None:
    """
    Incremental sync entrypoint for Celery worker (runs async logic via asyncio.run).
    Processes one batch (default 100 nodes).
    """
    asyncio.run(_sync_batch_once())


@celery.task(name="sync_wiki_full")
def sync_wiki_full(max_batches: int = 200) -> None:
    """
    Full sync: process multiple batches in sequence until no more nodes to sync.
    Useful for initial sync or catching up after downtime.
    
    Args:
        max_batches: Maximum number of batches to process (safety limit).
                     Each batch = 100 nodes. Default 200 = 20,000 nodes max.
    """
    async def run_multiple_batches() -> None:
        total_nodes_processed = 0
        total_edges_added = 0
        
        for batch_num in range(1, max_batches + 1):
            nodes_processed, edges_added = await _sync_batch_once(batch_size=100)
            
            if nodes_processed == 0:
                break
            
            total_nodes_processed += nodes_processed
            total_edges_added += edges_added

    asyncio.run(run_multiple_batches())


async def _seed_from_file(path: Path) -> None:
    """Seed all names from a text file as nodes only (edges will be built by incremental sync)."""
    if not path.is_file():
        logger.warning("Seed file %s not found; skipping", path)
        return

    async with SessionLocal() as session:
        nodes_repo = NodesRepository(session)
        total_nodes = 0

        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                name = raw.strip()
                if not name:
                    continue

                await nodes_repo.upsert_by_title(name)
                total_nodes += 1

        await session.commit()
        logger.info(
            "Seeded from file %s: processed %d names (nodes only, edges via incremental sync)",
            path,
            total_nodes,
        )


@celery.task(name="seed_from_file")
def seed_from_file() -> None:
    """One-time seeding task: import names from seed file and call Wikipedia for each."""
    path = Path(settings.seed_file_path)
    asyncio.run(_seed_from_file(path))


async def _import_graph_from_file(path: Path) -> None:
    """
    Import nodes and edges from an existing graph.json file.

    The file is expected to have the same structure as the original Go project:
    {
      "Person A": ["Person B", "Person C", ...],
      "Person B": ["Person A", ...],
      ...
    }
    """
    if not path.is_file():
        logger.warning("Graph file %s not found; skipping import", path)
        return

    logger.info("Importing graph from %s ...", path)

    raw: Dict[str, List[str]] = json.loads(path.read_text(encoding="utf-8"))

    async with SessionLocal() as session:
        nodes_repo = NodesRepository(session)
        edges_repo = EdgesRepository(session)

        # Only consider people that exist in seed_names.txt and have been seeded as nodes
        valid_names = _load_valid_names()

        total_edges = 0

        for src_title, targets in raw.items():
            # Only use sources that are in the seed list and already exist as nodes
            if src_title not in valid_names:
                continue

            src_node = await nodes_repo.get_by_title(src_title)
            if src_node is None:
                continue

            # Some entries may have null/None or non-list values; treat as no edges
            if not isinstance(targets, list):
                continue

            for dst_title in targets or []:
                if not isinstance(dst_title, str):
                    continue

                # Only create edges to targets that are in the seed list and already seeded as nodes
                if dst_title not in valid_names:
                    continue

                dst_node = await nodes_repo.get_by_title(dst_title)
                if dst_node is None:
                    continue

                inserted = await edges_repo.add_edge(src_node.id, dst_node.id)
                if inserted:
                    total_edges += 1

        await session.commit()

    logger.info(
        "Graph import complete: edges inserted between seeded people: %d",
        total_edges,
    )


@celery.task(name="import_from_graph_json")
def import_from_graph_json() -> None:
    """One-time import: load nodes & edges directly from graph.json (no Wikipedia calls)."""
    path = Path(settings.graph_json_path)
    asyncio.run(_import_graph_from_file(path))


async def _sync_pending_people() -> tuple[int, int]:
    """
    Sync edges for people in the pending queue (added via /api/people/request).
    For each person in Redis set 'people:pending_sync':
    - Fetch outbound links from Wikipedia
    - Compare with existing nodes in DB
    - Create edges for any matches
    Returns: (people_processed, edges_added)
    """
    
    PENDING_SYNC_KEY = "people:pending_sync"
    
    async with SessionLocal() as session:
        nodes_repo = NodesRepository(session)
        edges_repo = EdgesRepository(session)
        
        try:
            pending_titles = await redis_client.smembers(PENDING_SYNC_KEY)
            pending_titles = [t.decode('utf-8') if isinstance(t, bytes) else t for t in pending_titles]
        except Exception as e:
            logger.error("Failed to get pending people from Redis: %s", e, exc_info=True)
            return (0, 0)
        
        if not pending_titles:
            return (0, 0)
        
        total_edges_added = 0
        processed_count = 0
        
        for title in pending_titles:
            try:
                node = await nodes_repo.get_by_title(title)
                if not node:
                    continue
                
                try:
                    outbound_titles = fetch_outbound_titles(title)
                except Exception as exc:
                    logger.error("Failed to fetch links for %s: %s", title, exc, exc_info=True)
                    continue
                
                node_edges = 0
                for linked_title in outbound_titles:
                    linked_node = await nodes_repo.get_by_title(linked_title)
                    if linked_node:
                        inserted = await edges_repo.add_edge(node.id, linked_node.id)
                        if inserted:
                            total_edges_added += 1
                            node_edges += 1
                
                processed_count += 1
                logger.info("Synced pending person '%s': added %d edges", title, node_edges)
                
            except Exception as e:
                logger.error("Error processing pending person %s: %s", title, e, exc_info=True)
                continue
        
        await session.commit()
        
        if processed_count > 0:
            try:
                await redis_client.srem(PENDING_SYNC_KEY, *pending_titles[:processed_count])
            except Exception as e:
                logger.warning("Failed to remove processed people from queue: %s", e)
        
        logger.info("Pending sync completed: processed %d people, added %d edges", processed_count, total_edges_added)
        return (processed_count, total_edges_added)


@celery.task(name="sync_pending_people")
def sync_pending_people() -> None:
    """
    Daily task to sync edges for people added via /api/people/request.
    Runs at midnight (00:00) daily.
    """
    asyncio.run(_sync_pending_people())


def _setup_beat_schedule() -> None:
    celery.conf.beat_schedule = {
        "daily-pending-sync": {
            "task": "sync_pending_people",
            "schedule": crontab(hour=0, minute=0),  # Every day at 00:00
        },
    }


_setup_beat_schedule()

