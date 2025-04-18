from sqlalchemy import String, DateTime, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from bubblemaps_bot.db.base import BASE

class TokenScreenshot(BASE):
    __tablename__ = "token_screenshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chain: Mapped[str] = mapped_column(String)
    token_id: Mapped[str] = mapped_column(String)
    update_date: Mapped[datetime] = mapped_column(DateTime)
    image_data: Mapped[bytes] = mapped_column(LargeBinary)