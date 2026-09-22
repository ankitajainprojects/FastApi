from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from functools import lru_cache

import models
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/books")
def create_book(
    title: str,
    author: str,
    price: int,
    db: Session = Depends(get_db)
):
    book = models.Book(
        title=title,
        author=author,
        price=price
    )

    db.add(book)
    db.commit()
    db.refresh(book)

    return book

@app.get("/books")
def get_books(
    db: Session = Depends(get_db)
):
    books = db.query(models.Book).all()

    if not books:
        raise HTTPException(
            status_code=404,
            detail="No books found"
        )

    return books


@lru_cache(maxsize=2)
@app.get("/books/{book_id}")
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    return book


@app.put("/books/{book_id}")
def update_book(
    book_id: int,
    title: str | None = None,
    author: str | None = None,
    price: int | None = None,
    db: Session = Depends(get_db)
):
    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    if title is not None:
        book.title = title

    if author is not None:
        book.author = author

    if price is not None:
        book.price = price

    db.commit()
    db.refresh(book)

    return book


@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    db.delete(book)
    db.commit()

    return {"message": "Book deleted successfully"}



