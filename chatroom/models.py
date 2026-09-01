from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String , Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True , autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    age : Mapped[Optional[int]] = mapped_column()

    messages: Mapped[List["Message"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User (ID = {self.id}, username={self.username})"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String(1000))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"Message (ID = {self.id}, user_id={self.user_id})"