from sqlalchemy import Boolean, Column, Integer, Numeric, String

from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
