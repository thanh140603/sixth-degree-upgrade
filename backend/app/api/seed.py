from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.nodes_repo import NodesRepository


class SeedRequest(BaseModel):
  names: List[str]


router = APIRouter(prefix="/api", tags=["seed"])


@router.post("/seed")
async def seed_people(payload: SeedRequest, db: AsyncSession = Depends(get_db)) -> dict:
  """
  Simple helper endpoint to seed the database with a list of names.
  Call once during development, then remove or protect in production.
  """
  repo = NodesRepository(db)
  count = 0
  for name in payload.names:
    name = name.strip()
    if not name:
      continue
    await repo.upsert_by_title(name)
    count += 1
  await db.commit()
  return {"inserted_or_updated": count}

