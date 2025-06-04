from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas import Book, BookCreate, BookUpdate
from crud import crud_book

router = APIRouter()


@router.post("/", response_model=Book)
def create_book(book: BookCreate):
    book_data = book.dict(exclude={'author_ids', 'genre_ids'})
    db_book = crud_book.create_with_relations(
        book_data,
        book.author_ids,
        book.genre_ids
    )
    if db_book:
        return crud_book.get_with_details(db_book['book_id'])
    raise HTTPException(status_code=400, detail="Failed to create book")


@router.get("/", response_model=List[Book])
def read_books(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        search: Optional[str] = None,
        author_id: Optional[int] = None,
        genre_id: Optional[int] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None
):
    if any([search, author_id, genre_id, year_from, year_to]):
        return crud_book.search(search, author_id, genre_id, year_from, year_to)
    return crud_book.get_all(skip=skip, limit=limit)


@router.get("/{book_id}", response_model=Book)
def read_book(book_id: int):
    db_book = crud_book.get_with_details(book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book


@router.put("/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookUpdate):
    book_data = book.dict(exclude={'author_ids', 'genre_ids'}, exclude_unset=True)
    db_book = crud_book.update_with_relations(
        book_id,
        book_data,
        book.author_ids,
        book.genre_ids
    )
    if db_book:
        return crud_book.get_with_details(book_id)
    raise HTTPException(status_code=404, detail="Book not found")


@router.delete("/{book_id}")
def delete_book(book_id: int):
    if crud_book.delete(book_id):
        return {"message": "Book deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found")


@router.get("/statistics/summary")
def get_statistics():
    total_books = crud_book.count()

    status_query = """
        SELECT status, COUNT(*) as count
        FROM books
        GROUP BY status
    """
    from database import execute_query
    books_by_status = execute_query(status_query)

    genre_query = """
        SELECT g.genre_name, COUNT(DISTINCT bg.book_id) as count
        FROM genres g
        JOIN books_genres bg ON g.genre_id = bg.genre_id
        GROUP BY g.genre_id, g.genre_name
        ORDER BY count DESC
        LIMIT 10
    """
    top_genres = execute_query(genre_query)

    author_query = """
        SELECT CONCAT(a.first_name, ' ', a.last_name) as author_name, 
               COUNT(DISTINCT ba.book_id) as count
        FROM authors a
        JOIN books_authors ba ON a.author_id = ba.author_id
        GROUP BY a.author_id, author_name
        ORDER BY count DESC
        LIMIT 10
    """
    top_authors = execute_query(author_query)

    rating_query = """
        SELECT AVG(rating) as avg_rating, COUNT(*) as total_reviews
        FROM reviews
    """
    rating_stats = execute_query(rating_query, fetch_one=True)

    return {
        "total_books": total_books,
        "books_by_status": {item['status']: item['count'] for item in books_by_status},
        "top_genres": top_genres,
        "top_authors": top_authors,
        "average_rating": float(rating_stats['avg_rating'] or 0),
        "total_reviews": rating_stats['total_reviews']
    }