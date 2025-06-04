from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from schemas import Reader, ReaderCreate, ReaderUpdate
from crud import crud_reader
from database import execute_query

router = APIRouter()


@router.post("/register", response_model=Reader)
def register_reader(reader: ReaderCreate):
    existing = execute_query(
        "SELECT reader_id FROM readers WHERE email = %s",
        (reader.email,),
        fetch_one=True
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_reader = crud_reader.create(**reader.dict())
    if db_reader:
        db_reader.pop('password_hash', None)
        return db_reader
    raise HTTPException(status_code=400, detail="Failed to create reader")


@router.post("/login")
def login(email: str, password: str):
    reader = crud_reader.authenticate(email, password)
    if not reader:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    reader.pop('password_hash', None)
    return {
        "message": "Login successful",
        "reader": reader
    }


@router.get("/", response_model=List[Reader])
def read_readers(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000)
):
    readers = crud_reader.get_all(skip=skip, limit=limit)
    for reader in readers:
        reader.pop('password_hash', None)
    return readers


@router.get("/{reader_id}", response_model=Reader)
def read_reader(reader_id: int):
    db_reader = crud_reader.get(reader_id)
    if db_reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    db_reader.pop('password_hash', None)
    return db_reader


@router.get("/{reader_id}/statistics")
def read_reader_statistics(reader_id: int):
    return crud_reader.get_statistics(reader_id)


@router.put("/{reader_id}", response_model=Reader)
def update_reader(reader_id: int, reader: ReaderUpdate):
    update_data = reader.dict(exclude_unset=True)
    if 'password' in update_data:
        from crud import pwd_context
        update_data['password_hash'] = pwd_context.hash(update_data.pop('password'))

    db_reader = crud_reader.update(reader_id, **update_data)
    if db_reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    db_reader.pop('password_hash', None)
    return db_reader


@router.delete("/{reader_id}")
def delete_reader(reader_id: int):
    db_reader = crud_reader.update(reader_id, is_active=False)
    if db_reader:
        return {"message": "Reader deactivated successfully"}
    raise HTTPException(status_code=404, detail="Reader not found")