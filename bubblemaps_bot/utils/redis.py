import json
from redis.asyncio import Redis
from bubblemaps_bot.utils.yaml import load_config

config = load_config("config.yaml")
redis_config = config.get("redis", {})

REDIS_ENABLED: bool = redis_config.get("enabled", False)
REDIS_TTL: int = redis_config.get("ttl", 3600)
REDIS_HOST: str = redis_config.get("host", "localhost")
REDIS_PORT: int = redis_config.get("port", 6379)
REDIS_DB: int = redis_config.get("db", 0)
SCREENSHOT_CACHE_ENABLED: bool = redis_config.get("screenshot_cache", False) if REDIS_ENABLED else False


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
