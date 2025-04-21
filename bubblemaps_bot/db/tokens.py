from sqlalchemy import select
from bubblemaps_bot.models.tokens import SuccessfulToken
from bubblemaps_bot.db.session import async_session


async def add_successful_token(chain: str, token_id: str):
    """
    Add a successful token to the database if it doesn't already exist.
    Args:
        chain: Blockchain network identifier (e.g., 'eth').
        token_id: Token address.
    """
    async with async_session() as session:
        exists = await session.scalar(
            select(SuccessfulToken).where(
                SuccessfulToken.chain == chain,
                SuccessfulToken.token_id == token_id
            )
        )
        if not exists:
            session.add(SuccessfulToken(chain=chain, token_id=token_id))
            await session.commit()


async def get_all_successful_tokens():
    """
    Retrieve all successful tokens from the database.
    Returns:
        List of SuccessfulToken objects.
    """
    async with async_session() as session:
        result = await session.execute(select(SuccessfulToken))
        return result.scalars().all()


async def get_successful_token(token_id: str, chain: str = None) -> SuccessfulToken | None:
    """
    Query the database for a specific successful token by token_id and optionally by chain.
    Args:
        token_id: Token address to query.
        chain: Blockchain network identifier (e.g., 'eth'). If None, returns first match.
    Returns:
        SuccessfulToken object if found, else None.
    """
    async with async_session() as session:
        query = select(SuccessfulToken).where(SuccessfulToken.token_id.ilike(token_id))
        if chain:
            query = query.where(SuccessfulToken.chain == chain)
        result = await session.execute(query)
        return result.scalar_one_or_none()