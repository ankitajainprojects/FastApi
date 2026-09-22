from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from functools import lru_cache

import models
from database import Base, engine, get_db, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI()


@lru_cache(maxsize=2)
def get_book_cached(book_id: int):
    db = SessionLocal()

    try:
        logger.info(
            "CACHE MISS for book_id=%s hence querying DB",
            book_id
        )

        book = (
            db.query(models.Book)
            .filter(models.Book.id == book_id)
            .first()
        )

        if not book:
            return None

        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "price": book.price
        }

    finally:
        db.close()

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

    get_book_cached.cache_clear()
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


@app.get("/books/{book_id}")
def get_book(book_id: int):

    book = get_book_cached(book_id)

    if book is None:
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

    get_book_cached.cache_clear()

    return {"message": "Book deleted successfully"}



