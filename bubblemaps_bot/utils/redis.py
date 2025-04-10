import json
from redis.asyncio import Redis
from bubblemaps_bot import REDIS_ENABLED, REDIS_TTL, REDIS_HOST, REDIS_PORT, REDIS_DB


redis: Redis | None = None

if REDIS_ENABLED:
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

async def get_cache(key: str) -> dict | None:
    if not redis:
        return None
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        print(f"Error fetching cache for key {key}: {e}")
        return None

async def set_cache(key: str, value: dict, ttl: int = None) -> None:
    if not redis:
        return
    try:
        await redis.set(key, json.dumps(value), ex=ttl or REDIS_TTL)
    except Exception as e:
        print(f"Error setting cache for key {key}: {e}")
