import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Node


class NodesRepository:
    """Data-access for nodes (Single Responsibility: persistence only)."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_title(self, title: str) -> Node | None:
        res = await self._db.execute(select(Node).where(Node.title == title))
        return res.scalar_one_or_none()

    async def get_titles(self, limit: int = 20000) -> list[str]:
        res = await self._db.execute(select(Node.title).limit(limit))
        return [r[0] for r in res.all()]

    async def get_batch_for_sync(self, limit: int = 50) -> list[Node]:
        """Pick a batch of nodes to refresh from Wikipedia."""
        res = await self._db.execute(
            select(Node).order_by(Node.last_seen_at.asc()).limit(limit)
        )
        return list(res.scalars().all())

    async def upsert_by_title(self, title: str, page_id: int | None = None) -> Node:
        existing = await self.get_by_title(title)
        now = datetime.now(timezone.utc)
        if existing:
            existing.last_seen_at = now
            if page_id is not None and existing.page_id is None:
                existing.page_id = page_id
            return existing

        node = Node(title=title, page_id=page_id, last_seen_at=now)
        self._db.add(node)
        return node

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Node]:
        if not ids:
            return []
        res = await self._db.execute(select(Node).where(Node.id.in_(ids)))
        return list(res.scalars().all())

