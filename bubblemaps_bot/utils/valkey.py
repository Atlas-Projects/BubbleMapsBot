import json

from telegram.ext import Application
from valkey.asyncio import Valkey

from bubblemaps_bot import (
    VALKEY_DB,
    VALKEY_ENABLED,
    VALKEY_HOST,
    VALKEY_PORT,
    VALKEY_TTL,
    logger,
)

valkey: Valkey | None = None

if VALKEY_ENABLED:
    valkey = Valkey(
        host=VALKEY_HOST, port=VALKEY_PORT, db=VALKEY_DB, decode_responses=True
    )


async def get_cache(key: str) -> dict | None:
    """
    Retrieve a cached value from Valkey by key.
    Args:
        key: Cache key.
    Returns:
        dict: Cached value if found, None otherwise.
    """
    if not valkey:
        return None
    try:
        raw = await valkey.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.error(f"Error fetching cache for key {key}: {e}")
        return None


async def set_cache(key: str, value: dict, ttl: int = None) -> None:
    """
    Store a value in Valkey with an optional TTL.
    Args:
        key: Cache key.
        value: Dictionary to cache.
        ttl: Time-to-live in seconds (defaults to VALKEY_TTL if None).
    """
    if not valkey:
        return
    try:
        await valkey.set(key, json.dumps(value), ex=ttl or VALKEY_TTL)
    except Exception as e:
        logger.error(f"Error setting cache for key {key}: {e}")


async def shutdown_valkey(_: Application) -> None:
    """
    Close the Valkey connection pool during application shutdown.
    Args:
        _: Telegram Application instance (unused).
    """
    if valkey:
        await valkey.aclose(close_connection_pool=True)