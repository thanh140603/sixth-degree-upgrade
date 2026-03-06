FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir \
    fastapi~=0.115.0 \
    "uvicorn[standard]~=0.30.0" \
    "pydantic~=2.7.0" \
    "pydantic-settings~=2.3.0" \
    "sqlalchemy~=2.0.30" \
    "psycopg[binary]~=3.1.19" \
    "alembic~=1.13.2" \
    "httpx~=0.27.0" \
    "tenacity~=8.3.0" \
    "celery~=5.4.0" \
    "redis~=5.0.4"

COPY backend/app /app/app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

