from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


async def get_db_session() -> AsyncSession:
    async for s in get_db():
        return s

