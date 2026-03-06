import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.nodes_repo import NodesRepository
from app.core.redis_client import redis_client
from app.wiki.person_detector import is_person_page

logger = logging.getLogger(__name__)

POPULARITY_KEY = "people:popularity"
PENDING_SYNC_KEY = "people:pending_sync"


class PeopleService:
    """Application use-cases around people listing/searching."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._nodes = NodesRepository(db)

    async def list_people(self, limit: int = 20000) -> list[str]:
        """
        Return list of people titles, sorted by popularity (from Redis)
        then alphabetically as a tiebreaker.
        """
        names = await self._nodes.get_titles(limit=limit)
        if not names:
            return []

        try:
            scores = await redis_client.zmscore(POPULARITY_KEY, names)
        except Exception:
            return names

        combined = list(zip(names, scores))

        combined.sort(key=lambda item: (-(item[1] or 0), item[0]))

        return [name for name, _ in combined]

    async def request_new_person(self, name: str) -> dict:
        """
        Check if a person exists on Wikipedia, create node if valid, and add to pending sync queue.
        
        Returns:
            {
                "success": bool,
                "message": str,
                "exists": bool  # True if Wikipedia page exists and is a person
            }
        """
        title = name.strip()
        if not title:
            return {"success": False, "message": "Name cannot be empty", "exists": False}

        existing = await self._nodes.get_by_title(title)
        if existing:
            return {"success": True, "message": "Person already exists in database", "exists": True}

        # Check Wikipedia + Wikidata to see if it's a person
        try:
            is_person = is_person_page(title, seed_names=None)
        except Exception as e:
            logger.error("Error checking if %s is a person: %s", title, e, exc_info=True)
            return {"success": False, "message": f"Error checking Wikipedia: {str(e)}", "exists": False}

        if not is_person:
            return {"success": False, "message": "No Wikipedia page found for this person", "exists": False}

        # Create node in DB
        try:
            await self._nodes.upsert_by_title(title)
            await self._db.commit()
        except Exception as e:
            await self._db.rollback()
            logger.error("Error creating node for %s: %s", title, e, exc_info=True)
            return {"success": False, "message": f"Error creating person: {str(e)}", "exists": True}

        # Add to pending sync queue (Redis set)
        try:
            await redis_client.sadd(PENDING_SYNC_KEY, title)
        except Exception as e:
            logger.warning("Failed to add %s to pending sync queue: %s", title, e)

        return {
            "success": True,
            "message": f"Person '{title}' has been added. Edges will be updated daily at midnight.",
            "exists": True,
        }
