from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String , Integer
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URL = "sqlite:///./sqlite.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True , autoincrement=True)
    first_name : Mapped[str] = mapped_column(String(80))
    last_name : Mapped[Optional[str]] = mapped_column(String(120))
    age : Mapped[Optional[int]] = mapped_column()

    def __repr__(self) -> str:
        return f"User (ID = {self.id}) , first_name={self.first_name} , last_name={self.last_name}"

Base.metadata.create_all(engine)

