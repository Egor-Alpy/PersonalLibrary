from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime

class PublisherBase(BaseModel):
    publisher_name: str
    country: Optional[str] = None
    city: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    contacts: Optional[str] = None

class PublisherCreate(PublisherBase):
    pass

class PublisherUpdate(PublisherBase):
    publisher_name: Optional[str] = None

class Publisher(PublisherBase):
    publisher_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SeriesBase(BaseModel):
    series_name: str
    description: Optional[str] = None
    publisher_id: Optional[int] = None

class SeriesCreate(SeriesBase):
    pass

class SeriesUpdate(SeriesBase):
    series_name: Optional[str] = None

class Series(SeriesBase):
    series_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    isbn: Optional[str] = None
    publisher_id: Optional[int] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    pages_count: Optional[int] = Field(None, gt=0)
    language: str = "Русский"
    description: Optional[str] = None
    storage_location: Optional[str] = None
    acquisition_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    condition: Optional[str] = Field(None, pattern="^(новая|хорошее|удовлетворительное)$")
    format: Optional[str] = Field(None, pattern="^(твердый переплет|мягкая обложка|электронная)$")
    status: str = Field("в библиотеке", pattern="^(в библиотеке|одолжена|утеряна)$")
    series_id: Optional[int] = None
    series_number: Optional[int] = None

class BookCreate(BookBase):
    author_ids: List[int] = []
    genre_ids: List[int] = []

class BookUpdate(BookBase):
    title: Optional[str] = None
    status: Optional[str] = None
    author_ids: Optional[List[int]] = None
    genre_ids: Optional[List[int]] = None

class Book(BookBase):
    book_id: int
    created_at: datetime
    updated_at: datetime
    avg_rating: Optional[float] = 0
    review_count: Optional[int] = 0
    authors: Optional[List['Author']] = []
    genres: Optional[List['Genre']] = []

    class Config:
        from_attributes = True

class AuthorBase(BaseModel):
    first_name: Optional[str] = None
    last_name: str
    pseudonym: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    country: Optional[str] = None
    biography: Optional[str] = None

    @validator('death_date')
    def death_date_must_be_after_birth(cls, v, values):
        if v and 'birth_date' in values and values['birth_date']:
            if v <= values['birth_date']:
                raise ValueError('death_date must be after birth_date')
        return v

class AuthorCreate(AuthorBase):
    pass

class AuthorUpdate(AuthorBase):
    last_name: Optional[str] = None

class Author(AuthorBase):
    author_id: int
    created_at: datetime
    books_count: Optional[int] = 0

    class Config:
        from_attributes = True

class GenreBase(BaseModel):
    genre_name: str
    description: Optional[str] = None
    parent_genre_id: Optional[int] = None

class GenreCreate(GenreBase):
    pass

class GenreUpdate(GenreBase):
    genre_name: Optional[str] = None

class Genre(GenreBase):
    genre_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ReaderBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    preferences: Optional[str] = None

class ReaderCreate(ReaderBase):
    password: str

class ReaderUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferences: Optional[str] = None
    password: Optional[str] = None

class Reader(ReaderBase):
    reader_id: int
    registration_date: date
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    book_id: int
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    favorite_quotes: Optional[str] = None
    reading_status: str = "прочитано"

    @validator('end_date')
    def end_date_must_be_after_start(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after or equal to start_date')
        return v

class ReviewCreate(ReviewBase):
    reader_id: int

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    favorite_quotes: Optional[str] = None
    reading_status: Optional[str] = None

class Review(ReviewBase):
    review_id: int
    reader_id: int
    review_date: date
    created_at: datetime
    book_title: Optional[str] = None
    reader_name: Optional[str] = None

    class Config:
        from_attributes = True

class BookStatistics(BaseModel):
    total_books: int
    books_read: int
    average_rating: float
    books_by_status: dict
    top_genres: List[dict]
    top_authors: List[dict]
    reading_progress: List[dict]