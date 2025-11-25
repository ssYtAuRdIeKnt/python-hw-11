import os
from typing import List
from sqlalchemy import create_engine, String, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class UserItem(Base):
    __tablename__ = "user_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


def get_top_items_for_user(user_email: str, limit: int = 3) -> List[str]:
    with Session(engine) as session:
        rows = session.query(UserItem.title)\
            .filter(UserItem.user_email == user_email)\
            .order_by(UserItem.id.desc())\
            .limit(limit).all()
    return [title for (title,) in rows]