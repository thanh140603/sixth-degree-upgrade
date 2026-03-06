import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Edge


class EdgesRepository:
    """Data-access for edges (Single Responsibility: persistence only)."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add_edge(self, src_id: uuid.UUID, dst_id: uuid.UUID) -> bool:
        if dst_id is None:
            return False

        res = await self._db.execute(
            select(Edge).where(Edge.src_id == src_id, Edge.dst_id == dst_id).limit(1)
        )
        if res.scalar_one_or_none():
            return False
        self._db.add(Edge(src_id=src_id, dst_id=dst_id))
        return True

    async def get_neighbors(self, src_ids: list[uuid.UUID]) -> list[tuple[uuid.UUID, uuid.UUID]]:
        if not src_ids:
            return []
        res = await self._db.execute(select(Edge.src_id, Edge.dst_id).where(Edge.src_id.in_(src_ids)))
        return list(res.all())

