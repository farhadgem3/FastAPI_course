from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String , Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True , autoincrement=True)
    first_name : Mapped[str] = mapped_column(String(80))
    last_name : Mapped[Optional[str]] = mapped_column(String(120))
    age : Mapped[Optional[int]] = mapped_column()

    def __repr__(self) -> str:
        return f"User (ID = {self.id}) , first_name={self.first_name} , last_name={self.last_name}"