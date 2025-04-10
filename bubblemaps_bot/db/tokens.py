from sqlalchemy import select
from bubblemaps_bot.models.tokens import SuccessfulToken
from bubblemaps_bot.db.session import async_session

async def add_successful_token(chain: str, token_id: str):
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
    async with async_session() as session:
        result = await session.execute(select(SuccessfulToken))
        return result.scalars().all()
