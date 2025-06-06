from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from bubblemaps_bot.models.screenshot import TokenScreenshot
from bubblemaps_bot.db.session import async_session


async def get_token_screenshot(chain: str, token_id: str) -> TokenScreenshot | None:
    """
    Retrieve a token screenshot from the database by chain and token ID.
    Args:
        chain: Blockchain network identifier (e.g., 'eth').
        token_id: Token address.
    Returns:
        TokenScreenshot object if found, else None.
    """
    async with async_session() as session:
        result = await session.execute(
            select(TokenScreenshot).where(
                TokenScreenshot.chain == chain,
                TokenScreenshot.token_id == token_id
            )
        )
        return result.scalar_one_or_none()


async def upsert_token_screenshot(chain: str, token_id: str, update_date: datetime, image_data: bytes):
    """
    Insert or update a token screenshot in the database.
    Args:
        chain: Blockchain network identifier (e.g., 'eth').
        token_id: Token address.
        update_date: Timestamp of the screenshot update.
        image_data: Binary image data of the screenshot.
    """
    async with async_session() as session:
        existing = await session.execute(
            select(TokenScreenshot).where(
                TokenScreenshot.chain == chain,
                TokenScreenshot.token_id == token_id
            )
        )
        screenshot = existing.scalar_one_or_none()

        if screenshot:
            screenshot.update_date = update_date
            screenshot.image_data = image_data
        else:
            screenshot = TokenScreenshot(
                chain=chain,
                token_id=token_id,
                update_date=update_date,
                image_data=image_data
            )
            session.add(screenshot)

        await session.commit()