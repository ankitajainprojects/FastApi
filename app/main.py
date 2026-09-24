from fastapi import Depends, FastAPI, HTTPException, APIRouter, status
from sqlalchemy.orm import Session
from functools import lru_cache
import secrets
import models
from database import Base, engine, get_db, SessionLocal
import logging
from auth import auth_dependency, AUTH_TYPE, create_access_token, EXPECTED_USERNAME, EXPECTED_PASSWORD


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/auth/login", tags=["Authentication"])
def login( username: str, password: str, ): 
    if AUTH_TYPE != "jwt":
        raise HTTPException( status_code=status.HTTP_404_NOT_FOUND,
                            detail="JWT authentication is not enabled", ) 
    if not EXPECTED_USERNAME or not EXPECTED_PASSWORD: 
        raise RuntimeError( "BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD " "must be defined in .env" ) 
    username_correct = secrets.compare_digest( username, EXPECTED_USERNAME ) 
    password_correct = secrets.compare_digest( password, EXPECTED_PASSWORD )
    if not username_correct or not password_correct: 
        raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Incorrect username or password", ) 
    access_token = create_access_token(username) 
    return { "access_token": access_token, "token_type": "bearer", }
    

router = APIRouter( prefix="/books", tags=["Books"], dependencies=[ Depends(auth_dependency) ] )    


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

@router.post("")
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

@router.get("")
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


@router.get("/{book_id}")
def get_book(book_id: int):

    book = get_book_cached(book_id)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    
    return book

 

@router.put("/{book_id}")
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


@router.delete("/{book_id}")
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

app.include_router(router)


