import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.nodes_repo import NodesRepository
from app.services.path_service import PathService
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> None:
    await websocket.accept()
    service = PathService(db)
    nodes_repo = NodesRepository(db)

    level_queue: list[tuple[int, list]] = []

    def on_node_explored(level: int, node_id):
        pass

    async def process_level(level: int, node_ids: list):
        if not node_ids:
            return
        
        try:
            nodes = await nodes_repo.get_by_ids(node_ids)
            node_titles = [n.title for n in nodes]
            
            await websocket.send_json({
                "type": "level_explored",
                "data": {
                    "level": level,
                    "nodes": node_titles,
                },
            })
            
            for title in node_titles:
                await websocket.send_json({
                    "type": "node_explored",
                    "data": {
                        "level": level,
                        "node": title,
                        "nodesExploredAtLevel": len(node_titles),
                    },
                })
        except Exception as e:
            logger.error("Error in process_level: %s", e, exc_info=True)

    def on_level_done(level: int, node_ids: list):
        if not node_ids:
            return
        level_queue.append((level, node_ids))

    try:
        while True:
            data = await websocket.receive_json()
            start = data.get("startNode")
            end = data.get("endNode")
            if not start or not end:
                await websocket.send_json(
                    {"type": "error", "data": "startNode and endNode are required"}
                )
                continue

            # Increment popularity counters in Redis for start & end nodes
            try:
                await redis_client.zincrby("people:popularity", 1, start)
                await redis_client.zincrby("people:popularity", 1, end)
            except Exception as e:
                logger.error("Failed to update popularity counters in Redis: %s", e, exc_info=True)

            # Reset queue for new search
            level_queue.clear()
            
            try:
                path = await service.find_shortest_path_bfs(
                    start,
                    end,
                    on_level_done=on_level_done,
                    on_node_explored=on_node_explored,
                )
                
                # Process all explored levels
                for level, node_ids in level_queue:
                    await process_level(level, node_ids)
                
            except ValueError as exc:
                await websocket.send_json({"type": "error", "data": str(exc)})
                continue

            await websocket.send_json(
                {
                    "type": "path_found",
                    "data": {
                        "path": path,
                        "length": len(path),
                    },
                }
            )
    except WebSocketDisconnect:
        return

