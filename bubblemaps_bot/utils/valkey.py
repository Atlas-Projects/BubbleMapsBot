import json

from telegram.ext import Application
from valkey.asyncio import Valkey

from bubblemaps_bot import (
    VALKEY_DB,
    VALKEY_ENABLED,
    VALKEY_HOST,
    VALKEY_PORT,
    VALKEY_TTL,
)

valkey: Valkey | None = None

if VALKEY_ENABLED:
    valkey = Valkey(
        host=VALKEY_HOST, port=VALKEY_PORT, db=VALKEY_DB, decode_responses=True
    )


async def get_cache(key: str) -> dict | None:
    if not valkey:
        return None
    try:
        raw = await valkey.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        print(f"Error fetching cache for key {key}: {e}")
        return None


async def set_cache(key: str, value: dict, ttl: int = None) -> None:
    if not valkey:
        return
    try:
        await valkey.set(key, json.dumps(value), ex=ttl or VALKEY_TTL)
    except Exception as e:
        print(f"Error setting cache for key {key}: {e}")


async def shutdown_valkey(_: Application) -> None:
    if valkey:
        await valkey.aclose(close_connection_pool=True)
