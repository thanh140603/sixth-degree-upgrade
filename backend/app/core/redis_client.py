import redis.asyncio as redis

from app.core.settings import settings


# Shared async Redis client for the app.
# We use decode_responses=True to work with str instead of bytes.
redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)

