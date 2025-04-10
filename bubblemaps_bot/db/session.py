from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from bubblemaps_bot.db.base import BASE
from bubblemaps_bot import SCHEMA

engine = create_async_engine(SCHEMA, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(BASE.metadata.create_all)
