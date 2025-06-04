from fastapi import APIRouter, HTTPException, Query
from typing import List
from schemas import Genre, GenreCreate, GenreUpdate
from crud import crud_genre

router = APIRouter()

@router.post("/", response_model=Genre)
def create_genre(genre: GenreCreate):
    db_genre = crud_genre.create(**genre.dict())
    if db_genre:
        return db_genre
    raise HTTPException(status_code=400, detail="Failed to create genre")

@router.get("/", response_model=List[Genre])
def read_genres(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    return crud_genre.get_all(skip=skip, limit=limit)

@router.get("/hierarchy", response_model=List[Genre])
def read_genres_hierarchy():
    return crud_genre.get_hierarchy()

@router.get("/{genre_id}", response_model=Genre)
def read_genre(genre_id: int):
    db_genre = crud_genre.get_with_books_count(genre_id)
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    return db_genre

@router.put("/{genre_id}", response_model=Genre)
def update_genre(genre_id: int, genre: GenreUpdate):
    db_genre = crud_genre.update(genre_id, **genre.dict(exclude_unset=True))
    if db_genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    return db_genre

@router.delete("/{genre_id}")
def delete_genre(genre_id: int):
    if crud_genre.delete(genre_id):
        return {"message": "Genre deleted successfully"}
    raise HTTPException(status_code=404, detail="Genre not found")