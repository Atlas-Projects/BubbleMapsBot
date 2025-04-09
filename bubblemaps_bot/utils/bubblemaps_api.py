import httpx
from bubblemaps_bot.utils.redis import get_cache, set_cache

API_URL = "https://api-legacy.bubblemaps.io/map-data"

async def fetch_map_data(token: str, chain: str):
    key = f"bubblemaps:{chain}:{token}"
    cached = await get_cache(key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params={"token": token, "chain": chain})
        if response.status_code == 200:
            data = response.json()
            await set_cache(key, data)
            return data
        else:
            return None
