import aiohttp
from bubblemaps_bot.utils.redis import get_cache, set_cache
from bubblemaps_bot.utils.yaml import load_config

TTL = load_config("config.yaml").get("redis", {}).get("ttl", 3600)

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
        print(f"Error fetching metadata: {e}")
        return None
