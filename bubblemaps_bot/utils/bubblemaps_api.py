import httpx

from bubblemaps_bot import BASE_API_URL
from bubblemaps_bot.utils.valkey import get_cache, set_cache


async def fetch_map_data(token: str, chain: str):
    key = f"bubblemaps:{chain}:{token}"
    cached = await get_cache(key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        response = await client.get(
            BASE_API_URL, params={"token": token, "chain": chain}
        )
        if response.status_code == 200:
            data = response.json()
            await set_cache(key, data)
            return data
        else:
            return None


async def fetch_address_details(token: str, chain: str, address: str):
    """
    Fetch details of a specific address from the Bubblemaps API data.

    Args:
        token (str): Token address (e.g., '0x19de6b897ed14a376dda0fe53a5420d2ac828a28')
        chain (str): Blockchain chain (e.g., 'eth')
        address (str): Address to look up (e.g., '0x1ae3739e17d8500f2b2d80086ed092596a116e0b')

    Returns:
        dict: Details of the address if found, None otherwise
    """
    map_data = await fetch_map_data(token, chain)
    if not map_data:
        return None

    for node in map_data.get("nodes", []):
        if node["address"].lower() == address.lower():  # Case-insensitive comparison
            return node

    return None


async def fetch_distribution(token: str, chain: str):
    """
    Fetch and sort the distribution of token holdings in decreasing order by amount.

    Args:
        token (str): Token address
        chain (str): Blockchain chain

    Returns:
        list: Sorted list of nodes by amount in descending order, or None if data unavailable
    """
    map_data = await fetch_map_data(token, chain)
    if not map_data:
        return None

    nodes = map_data.get("nodes", [])
    sorted_nodes = sorted(nodes, key=lambda x: x.get("amount", 0), reverse=True)
    return sorted_nodes
