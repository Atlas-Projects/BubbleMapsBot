from sqlalchemy import select
from bubblemaps_bot.db.session import async_session
from bubblemaps_bot.models.users import User

async def add_user_if_not_exists(user_id: int):
    async with async_session() as session:
        exists = await session.scalar(select(User).where(User.user_id == user_id))
        if not exists:
            session.add(User(user_id=user_id))
            await session.commit()
