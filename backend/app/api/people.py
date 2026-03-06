from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.people_service import PeopleService

router = APIRouter(prefix="/api", tags=["people"])


class CreatePersonRequest(BaseModel):
    name: str


@router.get("/people")
async def get_people(db: AsyncSession = Depends(get_db)) -> dict:
    service = PeopleService(db)
    people = await service.list_people()
    return {"people": [{"name": p} for p in people]}


@router.post("/people/request")
async def request_new_person(
    request: CreatePersonRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request to add a new person to the system.
    Checks Wikipedia, creates node if valid, and adds to daily sync queue.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Received request to create person: %s", request.name)
    service = PeopleService(db)
    result = await service.request_new_person(request.name)
    
    logger.info("Result: success=%s, message=%s", result.get("success"), result.get("message"))
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

