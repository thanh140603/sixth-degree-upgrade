from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cleanup, health, people, seed, ws
from app.core.settings import settings
from app.db.base import Base
from app.db.session import engine


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # CORS
    origins = [o.strip() for o in settings.cors_allow_origins.split(",")] if settings.cors_allow_origins else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(people.router)
    app.include_router(ws.router)
    app.include_router(seed.router)
    app.include_router(cleanup.router)

    @app.on_event("startup")
    async def on_startup() -> None:  
        """Create database tables if they do not exist yet."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    return app


app = create_app()

