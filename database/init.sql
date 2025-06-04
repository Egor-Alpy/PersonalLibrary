CREATE DATABASE personal_library
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ru_RU.UTF-8'
    LC_CTYPE = 'ru_RU.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c personal_library;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE publishers (
    publisher_id SERIAL PRIMARY KEY,
    publisher_name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    city VARCHAR(100),
    founded_year INTEGER,
    website VARCHAR(255),
    contacts VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE series (
    series_id SERIAL PRIMARY KEY,
    series_name VARCHAR(200) NOT NULL,
    description TEXT,
    publisher_id INTEGER REFERENCES publishers(publisher_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    isbn VARCHAR(17) UNIQUE,
    publisher_id INTEGER REFERENCES publishers(publisher_id),
    publication_year INTEGER CHECK (publication_year >= 1000 AND publication_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    pages_count INTEGER CHECK (pages_count > 0),
    language VARCHAR(50) DEFAULT 'Русский',
    description TEXT,
    storage_location VARCHAR(100),
    acquisition_date DATE DEFAULT CURRENT_DATE,
    price DECIMAL(10,2) CHECK (price >= 0),
    condition VARCHAR(50) DEFAULT 'хорошее' CHECK (condition IN ('новая', 'хорошее', 'удовлетворительное')),
    format VARCHAR(50) DEFAULT 'твердый переплет' CHECK (format IN ('твердый переплет', 'мягкая обложка', 'электронная')),
    status VARCHAR(50) DEFAULT 'в библиотеке' CHECK (status IN ('в библиотеке', 'одолжена', 'утеряна')),
    series_id INTEGER REFERENCES series(series_id),
    series_number INTEGER,
    cover_image BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    pseudonym VARCHAR(100),
    birth_date DATE,
    death_date DATE CHECK (death_date IS NULL OR death_date > birth_date),
    country VARCHAR(100),
    biography TEXT,
    photo BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(255),
    parent_genre_id INTEGER REFERENCES genres(genre_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE readers (
    reader_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    registration_date DATE DEFAULT CURRENT_DATE,
    preferences TEXT,
    avatar BYTEA,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    reader_id INTEGER NOT NULL REFERENCES readers(reader_id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    start_date DATE,
    end_date DATE CHECK (end_date IS NULL OR end_date >= start_date),
    review_date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    favorite_quotes TEXT,
    reading_status VARCHAR(50) DEFAULT 'прочитано',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book_id, reader_id)
);

CREATE TABLE books_authors (
    book_id INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES authors(author_id),
    authorship_type VARCHAR(50) DEFAULT 'автор',
    PRIMARY KEY (book_id, author_id)
);

CREATE TABLE books_genres (
    book_id INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(genre_id),
    is_primary BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (book_id, genre_id)
);

CREATE INDEX idx_books_title ON books USING gin (title gin_trgm_ops);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_publisher ON books(publisher_id);
CREATE INDEX idx_books_series ON books(series_id);
CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_authors_name ON authors(last_name, first_name);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_reader ON reviews(reader_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE VIEW v_books_full AS
SELECT
    b.book_id,
    b.title,
    b.isbn,
    b.publication_year,
    b.pages_count,
    b.language,
    b.description,
    b.storage_location,
    b.acquisition_date,
    b.price,
    b.condition,
    b.format,
    b.status,
    b.series_number,
    p.publisher_name,
    s.series_name,
    COALESCE(AVG(r.rating), 0) as avg_rating,
    COUNT(DISTINCT r.review_id) as review_count
FROM books b
LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
LEFT JOIN series s ON b.series_id = s.series_id
LEFT JOIN reviews r ON b.book_id = r.book_id
GROUP BY b.book_id, p.publisher_name, s.series_name;

INSERT INTO genres (genre_name, description) VALUES
('Художественная литература', 'Произведения, созданные воображением автора'),
('Научная фантастика', 'Фантастика с научным обоснованием'),
('Детектив', 'Расследование преступлений'),
('Роман', 'Крупная форма эпической литературы'),
('Поэзия', 'Литература в стихотворной форме'),
('Научная литература', 'Научные труды и исследования'),
('Биография', 'Описание жизни человека'),
('История', 'Исторические произведения'),
('Психология', 'Литература о психологии человека'),
('Философия', 'Философские труды');

INSERT INTO publishers (publisher_name, country, city, founded_year) VAL