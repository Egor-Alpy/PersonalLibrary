from fastapi import APIRouter, HTTPException, Query
from typing import List
from schemas import Publisher, PublisherCreate, PublisherUpdate
from crud import crud_publisher

router = APIRouter()

@router.post("/", response_model=Publisher)
def create_publisher(publisher: PublisherCreate):
    db_publisher = crud_publisher.create(**publisher.dict())
    if db_publisher:
        return db_publisher
    raise HTTPException(status_code=400, detail="Failed to create publisher")

@router.get("/", response_model=List[Publisher])
def read_publishers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    return crud_publisher.get_all(skip=skip, limit=limit)

@router.get("/{publisher_id}", response_model=Publisher)
def read_publisher(publisher_id: int):
    db_publisher = crud_publisher.get_with_books_count(publisher_id)
    if db_publisher is None:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return db_publisher

@router.put("/{publisher_id}", response_model=Publisher)
def update_publisher(publisher_id: int, publisher: PublisherUpdate):
    db_publisher = crud_publisher.update(publisher_id, **publisher.dict(exclude_unset=True))
    if db_publisher is None:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return db_publisher

@router.delete("/{publisher_id}")
def delete_publisher(publisher_id: int):
    if crud_publisher.delete(publisher_id):
        return {"message": "Publisher deleted successfully"}
    raise HTTPException(status_code=404, detail="Publisher not found")