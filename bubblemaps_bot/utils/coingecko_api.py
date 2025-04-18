import aiohttp
import logging

logger = logging.getLogger(__name__)

async def get_market_data(chain: str, token_address: str) -> dict | None:
    """
    Fetch market data for a token from CoinGecko API.
    
    Args:
        chain (str): The blockchain platform (e.g., 'ethereum').
        token_address (str): The token contract address.
    
    Returns:
        dict | None: Market data dictionary or None if fetch fails.
    """
    async with aiohttp.ClientSession() as session:
        try:
            direct_url = f"https://api.coingecko.com/api/v3/coins/{chain}/contract/{token_address}"
            async with session.get(direct_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("market_data"):
                        return data
                else:
                    logger.warning(f"Direct lookup failed for {chain}/{token_address}: {response.status}")

            async with session.get(direct_url) as response:
                if response.status != 200 or not (data := await response.json()).get("id"):
                    logger.error(f"No valid coin ID found for {chain}/{token_address}")
                    return None

                coin_id = data["id"]
                market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
                async with session.get(market_url) as market_response:
                    if market_response.status == 200:
                        return await market_response.json()
                    else:
                        logger.error(f"Market data fetch failed for coin ID {coin_id}: {market_response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting market data for {chain}/{token_address}: {e}")
            return None