from sqlalchemy import Boolean, Column, Integer, Numeric, String, CheckConstraint

from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)


    __table_args__ = (
        CheckConstraint(
            "length(title) > 0",
            name="title_not_empty"
        ),
        CheckConstraint(
            "length(author) > 0",
            name="author_not_empty"
        ),
        CheckConstraint(
            "price > 0",
            name="price_positive"
        ),
    )