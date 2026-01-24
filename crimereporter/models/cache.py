from dataclasses import dataclass
from sqlalchemy import Integer, String, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from crimereporter.db.db import Base


@dataclass
class MessageCache(Base):
    __tablename__ = "message_cache"

    user_id: Mapped[str] = mapped_column(String)
    message_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    tokens: Mapped[int] = mapped_column(Integer)

    __table_args__ = (PrimaryKeyConstraint("user_id", "message_id"),)
