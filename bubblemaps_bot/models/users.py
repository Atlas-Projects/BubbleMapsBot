from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from bubblemaps_bot.db.base import BASE

class User(BASE):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
