from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas import Author, AuthorCreate, AuthorUpdate, Book
from crud import crud_author

router = APIRouter()

@router.post("/", response_model=Author)
def create_author(author: AuthorCreate):
    db_author = crud_author.create(**author.dict())
    if db_author:
        return crud_author.get_with_books_count(db_author['author_id'])
    raise HTTPException(status_code=400, detail="Failed to create author")

@router.get("/", response_model=List[Author])
def read_authors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None
):
    if search:
        return crud_author.search(search)
    return crud_author.get_all(skip=skip, limit=limit)

@router.get("/{author_id}", response_model=Author)
def read_author(author_id: int):
    db_author = crud_author.get_with_books_count(author_id)
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return db_author

@router.get("/{author_id}/books", response_model=List[Book])
def read_author_books(author_id: int):
    return crud_author.get_books(author_id)

@router.put("/{author_id}", response_model=Author)
def update_author(author_id: int, author: AuthorUpdate):
    db_author = crud_author.update(author_id, **author.dict(exclude_unset=True))
    if db_author:
        return crud_author.get_with_books_count(author_id)
    raise HTTPException(status_code=404, detail="Author not found")

@router.delete("/{author_id}")
def delete_author(author_id: int):
    if crud_author.delete(author_id):
        return {"message": "Author deleted successfully"}
    raise HTTPException(status_code=404, detail="Author not found")