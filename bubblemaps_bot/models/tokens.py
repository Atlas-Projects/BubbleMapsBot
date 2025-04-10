from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from bubblemaps_bot.db.base import BASE

class SuccessfulToken(BASE):
    __tablename__ = "successful_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chain: Mapped[str] = mapped_column(String)
    token_id: Mapped[str] = mapped_column(String)
