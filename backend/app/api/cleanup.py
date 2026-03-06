from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db.session import SessionLocal

router = APIRouter()


@router.post("/api/cleanup/all")
async def cleanup_all_data() -> dict:
    """
    WARNING: Deletes ALL data from nodes, edges, crawl_state, crawl_runs tables.
    Use with caution!
    """
    async with SessionLocal() as session:
        try:
            # Delete in order (respecting foreign keys)
            await session.execute(text("DELETE FROM edges"))
            await session.execute(text("DELETE FROM crawl_state"))
            await session.execute(text("DELETE FROM crawl_runs"))
            await session.execute(text("DELETE FROM nodes"))
            await session.commit()
            
            return {
                "message": "All data deleted successfully",
                "tables_cleared": ["nodes", "edges", "crawl_state", "crawl_runs"]
            }
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")


@router.post("/api/cleanup/edges-only")
async def cleanup_edges_only() -> dict:
    """
    Delete only edges (keeps nodes). Useful for rebuilding graph.
    """
    async with SessionLocal() as session:
        try:
            await session.execute(text("DELETE FROM edges"))
            await session.commit()
            
            return {
                "message": "Edges deleted successfully (nodes preserved)",
                "tables_cleared": ["edges"]
            }
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to cleanup edges: {str(e)}")
