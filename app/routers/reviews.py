from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas import Review, ReviewCreate, ReviewUpdate
from crud import crud_review
from database import execute_query

router = APIRouter()

@router.post("/", response_model=Review)
def create_review(review: ReviewCreate):
    db_review = crud_review.create(**review.dict())
    if db_review:
        return crud_review.get_with_details(db_review['review_id'])
    raise HTTPException(status_code=400, detail="Failed to create review")

@router.get("/", response_model=List[Review])
def read_reviews(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        book_id: Optional[int] = None,
        reader_id: Optional[int] = None
):
    if book_id:
        return crud_review.get_by_book(book_id, skip, limit)
    elif reader_id:
        return crud_review.get_by_reader(reader_id, skip, limit)
    return crud_review.get_all(skip=skip, limit=limit)

@router.get("/{review_id}", response_model=Review)
def read_review(review_id: int):
    db_review = crud_review.get_with_details(review_id)
    if db_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

@router.put("/{review_id}", response_model=Review)
def update_review(review_id: int, review: ReviewUpdate):
    db_review = crud_review.update(review_id, **review.dict(exclude_unset=True))
    if db_review:
        return crud_review.get_with_details(review_id)
    raise HTTPException(status_code=404, detail="Review not found")

@router.delete("/{review_id}")
def delete_review(review_id: int):
    if crud_review.delete(review_id):
        return {"message": "Review deleted successfully"}
    raise HTTPException(status_code=404, detail="Review not found")

@router.get("/statistics/reading-progress")
def get_reading_progress(reader_id: Optional[int] = None):
    if reader_id:
        query = """
            SELECT 
                EXTRACT(YEAR FROM r.end_date) as year,
                EXTRACT(MONTH FROM r.end_date) as month,
                COUNT(*) as books_read,
                SUM(b.pages_count) as pages_read,
                AVG(r.rating) as avg_rating
            FROM reviews r
            JOIN books b ON r.book_id = b.book_id
            WHERE r.reader_id = %s AND r.end_date IS NOT NULL
            GROUP BY year, month
            ORDER BY year DESC, month DESC
            LIMIT 12
        """
        return execute_query(query, (reader_id,))
    else:
        query = """
            SELECT 
                EXTRACT(YEAR FROM r.end_date) as year,
                EXTRACT(MONTH FROM r.end_date) as month,
                COUNT(*) as books_read,
                SUM(b.pages_count) as pages_read,
                AVG(r.rating) as avg_rating
            FROM reviews r
            JOIN books b ON r.book_id = b.book_id
            WHERE r.end_date IS NOT NULL
            GROUP BY year, month
            ORDER BY year DESC, month DESC
            LIMIT 12
        """
        return execute_query(query)