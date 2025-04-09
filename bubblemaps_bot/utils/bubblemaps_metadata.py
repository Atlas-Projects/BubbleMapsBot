import aiohttp
from bubblemaps_bot.utils.redis import get_cache, set_cache
from bubblemaps_bot.utils.yaml import load_config

config = load_config("config.yaml")
TTL = config.get("redis", {}).get("ttl", 3600)
SUPPORTED_CHAINS = config.get("bubblemaps", {}).get("supported_chains", [])

async def fetch_metadata(token: str, chain: str) -> dict | None:
    cache_key = f"metadata:{chain}:{token}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    url = f"https://api-legacy.bubblemaps.io/map-metadata?chain={chain}&token={token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "OK":
                        await set_cache(cache_key, data, ttl=TTL)
                    return data
    except Exception as e:
        print(f"Error fetching metadata for {chain}:{token}: {e}")
    return None

async def fetch_metadata_from_all_chains(token: str) -> tuple[str, dict] | None:
    for chain in SUPPORTED_CHAINS:
        data = await fetch_metadata(token, chain)
        if data and data.get("status") == "OK":
            return chain, data
    return None
