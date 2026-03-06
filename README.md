# Sixth Degree (Python + DB + Daily Wikipedia Sync)

Mục tiêu: clone ý tưởng “Six Degrees” nhưng backend dùng **Python/FastAPI**, dữ liệu lưu **PostgreSQL**, và có **daily job** gọi Wikipedia API để tự động thêm node/edge mới.

## Tech stack
- **API**: FastAPI + Uvicorn
- **DB**: PostgreSQL
- **Queue/Schedule**: Celery + Redis + Celery Beat
- **ORM/Migrations**: SQLAlchemy 2.x + Alembic

## Chạy local bằng Docker
1. Copy env:
   - Tạo file `sixth_degree_py/.env` dựa trên `sixth_degree_py/env.example`
2. Start:
   - `docker compose up --build`
3. API:
   - `http://localhost:8080/health`
   - REST: `GET http://localhost:8080/api/people`
   - WS: `ws://localhost:8080/ws`

## Notes
- Project này scaffold theo hướng SOLID: `api` (transport) → `services` (business logic) → `repositories` (data access) → `db/models`.
- Daily sync hiện được cấu hình qua Celery Beat; bạn chỉnh cron trong `.env`.

