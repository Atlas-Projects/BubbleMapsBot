import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import aiohttp

from bubblemaps_bot import MAP_METADATA_URL, SUPPORTED_CHAINS, VALKEY_TTL
from bubblemaps_bot.db.tokens import add_successful_token, get_successful_token
from bubblemaps_bot.utils.valkey import get_cache, set_cache

logger = logging.getLogger(__name__)


async def fetch_metadata_raw(chain: str, token: str) -> Optional[Dict[str, Any]]:
    """Fetch raw metadata from the BubbleMaps API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                MAP_METADATA_URL.format(chain=chain, token=token)
            ) as resp:
                logger.info(
                    f"[META] Fetching metadata for {chain}:{token} — Status: {resp.status}"
                )
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "OK":
                        return data
                    logger.warning(
                        f"[META] API returned non-OK status for {chain}:{token}"
                    )
                else:
                    logger.warning(
                        f"[META] Failed to fetch metadata for {chain}:{token}, status: {resp.status}"
                    )
    except Exception as e:
        logger.error(f"[API ERROR] {chain}:{token} - {e}")
    return None


async def fetch_token_metadata_update_date(
    chain: str, token: str
) -> Optional[datetime]:
    """Fetch the update date from token metadata."""
    data = await fetch_metadata_raw(chain, token)
    if data and (dt_update_str := data.get("dt_update")):
        return datetime.fromisoformat(dt_update_str)
    logger.warning(f"[META] No dt_update in metadata for {chain}:{token}")
    return None


async def fetch_metadata(token: str, chain: str) -> Optional[Dict[str, Any]]:
    """Fetch metadata with caching."""
    cache_key = f"metadata:{chain}:{token}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    data = await fetch_metadata_raw(chain, token)
    if data:
        await set_cache(cache_key, data, ttl=VALKEY_TTL)
    return data


async def fetch_metadata_from_all_chains(
    token: str,
) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Fetch metadata from all supported chains, prioritizing database-known successful tokens."""
    successful_token = await get_successful_token(token)
    if successful_token:
        chain = successful_token.chain
        logger.info(f"[META] Found successful token in database: {chain}:{token}")
        data = await fetch_metadata(token, chain)
        if data and data.get("status") == "OK":
            await add_successful_token(chain, token)
            return chain, data
        logger.warning(f"[META] Database-known chain {chain} failed for {token}")

    logger.info(
        f"[META] No successful token found in database for {token}, checking all chains"
    )
    for chain in SUPPORTED_CHAINS:
        data = await fetch_metadata(token, chain)
        if data and data.get("status") == "OK":
            await add_successful_token(chain, token)
            return chain, data
    return None
