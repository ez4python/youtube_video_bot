from sqlalchemy import BIGINT, String
from sqlalchemy.orm import Mapped, mapped_column
from db.config import AbstractClass


class User(AbstractClass):
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(BIGINT, autoincrement=True, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BIGINT, nullable=False, unique=True)
    lang: Mapped[str] = mapped_column(String, nullable=False)
    fullname: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user", nullable=False)
