# Sixth Degree (Python + DB + Daily Wikipedia Sync)

A clone of the "Six Degrees" idea: find connections between people via Wikipedia links. Backend uses **Python/FastAPI**, data is stored in **PostgreSQL**, with a **daily job** that calls the Wikipedia API to automatically add new nodes and edges.

## Tech Stack

- **API**: FastAPI + Uvicorn
- **DB**: PostgreSQL
- **Queue/Schedule**: Celery + Redis + Celery Beat
- **ORM/Migrations**: SQLAlchemy 2.x + Alembic

## Run Locally with Docker

1. **Copy env**:
   - Create `sixth_degree_py/.env` from `sixth_degree_py/env.example`
2. **Start**:
   - `docker compose up --build`
   
## Notes

- Project structure follows SOLID: `api` (transport) → `services` (business logic) → `repositories` (data access) → `db/models`.
- Daily sync is configured via Celery Beat; adjust the cron schedule in `.env`.
