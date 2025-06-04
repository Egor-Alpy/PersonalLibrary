from typing import List, Optional, Dict, Any
from database import execute_query, get_db_cursor
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDBase:
    def __init__(self, table: str, id_column: str = None):
        self.table = table
        self.id_column = id_column or f"{table[:-1]}_id"

    def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join(["%s"] * len(kwargs))
        values = tuple(kwargs.values())

        query = f"""
            INSERT INTO {self.table} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        return execute_query(query, values, fetch_one=True)

    def get(self, id: int) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {self.table} WHERE {self.id_column} = %s"
        return execute_query(query, (id,), fetch_one=True)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.table} ORDER BY {self.id_column} LIMIT %s OFFSET %s"
        return execute_query(query, (limit, skip))

    def update(self, id: int, **kwargs) -> Optional[Dict[str, Any]]:
        if not kwargs:
            return self.get(id)

        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = tuple(kwargs.values()) + (id,)

        query = f"""
            UPDATE {self.table}
            SET {set_clause}
            WHERE {self.id_column} = %s
            RETURNING *
        """
        return execute_query(query, values, fetch_one=True)

    def delete(self, id: int) -> bool:
        query = f"DELETE FROM {self.table} WHERE {self.id_column} = %s"
        return execute_query(query, (id,), fetch_all=False) > 0

    def count(self) -> int:
        query = f"SELECT COUNT(*) as count FROM {self.table}"
        result = execute_query(query, fetch_one=True)
        return result['count'] if result else 0


class CRUDBook(CRUDBase):
    def __init__(self):
        super().__init__("books", "book_id")

    def create_with_relations(self, book_data: dict, author_ids: List[int], genre_ids: List[int]) -> Optional[
        Dict[str, Any]]:
        with get_db_cursor() as cursor:
            columns = ", ".join(book_data.keys())
            placeholders = ", ".join(["%s"] * len(book_data))
            values = tuple(book_data.values())

            cursor.execute(f"""
                INSERT INTO books ({columns})
                VALUES ({placeholders})
                RETURNING *
            """, values)
            book = cursor.fetchone()

            if book and author_ids:
                for author_id in author_ids:
                    cursor.execute("""
                        INSERT INTO books_authors (book_id, author_id)
                        VALUES (%s, %s)
                    """, (book['book_id'], author_id))

            if book and genre_ids:
                for i, genre_id in enumerate(genre_ids):
                    cursor.execute("""
                        INSERT INTO books_genres (book_id, genre_id, is_primary)
                        VALUES (%s, %s, %s)
                    """, (book['book_id'], genre_id, i == 0))

            return book

    def get_with_details(self, book_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT 
                b.*,
                p.publisher_name,
                s.series_name,
                COALESCE(AVG(r.rating), 0) as avg_rating,
                COUNT(DISTINCT r.review_id) as review_count
            FROM books b
            LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
            LEFT JOIN series s ON b.series_id = s.series_id
            LEFT JOIN reviews r ON b.book_id = r.book_id
            WHERE b.book_id = %s
            GROUP BY b.book_id, p.publisher_name, s.series_name
        """
        book = execute_query(query, (book_id,), fetch_one=True)

        if book:
            authors_query = """
                SELECT a.* FROM authors a
                JOIN books_authors ba ON a.author_id = ba.author_id
                WHERE ba.book_id = %s
            """
            book['authors'] = execute_query(authors_query, (book_id,))

            genres_query = """
                SELECT g.* FROM genres g
                JOIN books_genres bg ON g.genre_id = bg.genre_id
                WHERE bg.book_id = %s
                ORDER BY bg.is_primary DESC
            """
            book['genres'] = execute_query(genres_query, (book_id,))

        return book

    def search(self, query: str, author_id: Optional[int] = None,
               genre_id: Optional[int] = None, year_from: Optional[int] = None,
               year_to: Optional[int] = None) -> List[Dict[str, Any]]:
        where_clauses = []
        params = []

        if query:
            where_clauses.append("(b.title ILIKE %s OR b.description ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])

        if author_id:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM books_authors ba WHERE ba.book_id = b.book_id AND ba.author_id = %s)")
            params.append(author_id)

        if genre_id:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM books_genres bg WHERE bg.book_id = b.book_id AND bg.genre_id = %s)")
            params.append(genre_id)

        if year_from:
            where_clauses.append("b.publication_year >= %s")
            params.append(year_from)

        if year_to:
            where_clauses.append("b.publication_year <= %s")
            params.append(year_to)

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
            SELECT b.*, 
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(DISTINCT r.review_id) as review_count
            FROM books b
            LEFT JOIN reviews r ON b.book_id = r.book_id
            WHERE {where_clause}
            GROUP BY b.book_id
            ORDER BY b.title
        """

        return execute_query(query, tuple(params))

    def update_with_relations(self, book_id: int, book_data: dict,
                              author_ids: Optional[List[int]] = None,
                              genre_ids: Optional[List[int]] = None) -> Optional[Dict[str, Any]]:
        with get_db_cursor() as cursor:
            if book_data:
                set_clause = ", ".join([f"{k} = %s" for k in book_data.keys()])
                values = tuple(book_data.values()) + (book_id,)

                cursor.execute(f"""
                    UPDATE books
                    SET {set_clause}
                    WHERE book_id = %s
                    RETURNING *
                """, values)
                book = cursor.fetchone()
            else:
                cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
                book = cursor.fetchone()

            if book and author_ids is not None:
                cursor.execute("DELETE FROM books_authors WHERE book_id = %s", (book_id,))
                for author_id in author_ids:
                    cursor.execute("""
                        INSERT INTO books_authors (book_id, author_id)
                        VALUES (%s, %s)
                    """, (book_id, author_id))

            if book and genre_ids is not None:
                cursor.execute("DELETE FROM books_genres WHERE book_id = %s", (book_id,))
                for i, genre_id in enumerate(genre_ids):
                    cursor.execute("""
                        INSERT INTO books_genres (book_id, genre_id, is_primary)
                        VALUES (%s, %s, %s)
                    """, (book_id, genre_id, i == 0))

            return book


class CRUDAuthor(CRUDBase):
    def __init__(self):
        super().__init__("authors", "author_id")

    def get_with_books_count(self, author_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT a.*, COUNT(DISTINCT ba.book_id) as books_count
            FROM authors a
            LEFT JOIN books_authors ba ON a.author_id = ba.author_id
            WHERE a.author_id = %s
            GROUP BY a.author_id
        """
        return execute_query(query, (author_id,), fetch_one=True)

    def get_books(self, author_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT b.* FROM books b
            JOIN books_authors ba ON b.book_id = ba.book_id
            WHERE ba.author_id = %s
            ORDER BY b.publication_year DESC
        """
        return execute_query(query, (author_id,))

    def search(self, query: str) -> List[Dict[str, Any]]:
        query_sql = """
            SELECT a.*, COUNT(DISTINCT ba.book_id) as books_count
            FROM authors a
            LEFT JOIN books_authors ba ON a.author_id = ba.author_id
            WHERE a.first_name ILIKE %s OR a.last_name ILIKE %s OR a.pseudonym ILIKE %s
            GROUP BY a.author_id
            ORDER BY a.last_name, a.first_name
        """
        search_pattern = f"%{query}%"
        return execute_query(query_sql, (search_pattern, search_pattern, search_pattern))


class CRUDGenre(CRUDBase):
    def __init__(self):
        super().__init__("genres", "genre_id")

    def get_with_books_count(self, genre_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT g.*, COUNT(DISTINCT bg.book_id) as books_count
            FROM genres g
            LEFT JOIN books_genres bg ON g.genre_id = bg.genre_id
            WHERE g.genre_id = %s
            GROUP BY g.genre_id
        """
        return execute_query(query, (genre_id,), fetch_one=True)

    def get_hierarchy(self) -> List[Dict[str, Any]]:
        query = """
            WITH RECURSIVE genre_tree AS (
                SELECT *, 0 as level
                FROM genres
                WHERE parent_genre_id IS NULL

                UNION ALL

                SELECT g.*, gt.level + 1
                FROM genres g
                JOIN genre_tree gt ON g.parent_genre_id = gt.genre_id
            )
            SELECT * FROM genre_tree
            ORDER BY level, genre_name
        """
        return execute_query(query)


class CRUDReader(CRUDBase):
    def __init__(self):
        super().__init__("readers", "reader_id")

    def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        if 'password' in kwargs:
            kwargs['password_hash'] = pwd_context.hash(kwargs.pop('password'))
        return super().create(**kwargs)

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM readers WHERE email = %s AND is_active = true"
        reader = execute_query(query, (email,), fetch_one=True)

        if reader and pwd_context.verify(password, reader['password_hash']):
            return reader
        return None

    def get_statistics(self, reader_id: int) -> Dict[str, Any]:
        stats_query = """
            SELECT 
                COUNT(DISTINCT r.book_id) as books_read,
                AVG(r.rating) as avg_rating,
                COUNT(DISTINCT EXTRACT(YEAR FROM r.end_date)) as years_active,
                COUNT(DISTINCT bg.genre_id) as genres_read,
                SUM(b.pages_count) as total_pages
            FROM reviews r
            JOIN books b ON r.book_id = b.book_id
            LEFT JOIN books_genres bg ON b.book_id = bg.book_id
            WHERE r.reader_id = %s AND r.end_date IS NOT NULL
        """
        stats = execute_query(stats_query, (reader_id,), fetch_one=True)

        genres_query = """
            SELECT g.genre_name, COUNT(*) as count, AVG(r.rating) as avg_rating
            FROM reviews r
            JOIN books_genres bg ON r.book_id = bg.book_id
            JOIN genres g ON bg.genre_id = g.genre_id
            WHERE r.reader_id = %s
            GROUP BY g.genre_id, g.genre_name
            ORDER BY count DESC, avg_rating DESC
            LIMIT 5
        """
        stats['favorite_genres'] = execute_query(genres_query, (reader_id,))

        authors_query = """
            SELECT CONCAT(a.first_name, ' ', a.last_name) as author_name, 
                   COUNT(*) as count, AVG(r.rating) as avg_rating
            FROM reviews r
            JOIN books_authors ba ON r.book_id = ba.book_id
            JOIN authors a ON ba.author_id = a.author_id
            WHERE r.reader_id = %s
            GROUP BY a.author_id, author_name
            ORDER BY count DESC, avg_rating DESC
            LIMIT 5
        """
        stats['favorite_authors'] = execute_query(authors_query, (reader_id,))

        return stats


class CRUDReview(CRUDBase):
    def __init__(self):
        super().__init__("reviews", "review_id")

    def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        check_query = """
            SELECT review_id FROM reviews 
            WHERE book_id = %s AND reader_id = %s
        """
        existing = execute_query(
            check_query,
            (kwargs.get('book_id'), kwargs.get('reader_id')),
            fetch_one=True
        )

        if existing:
            return self.update(existing['review_id'], **kwargs)

        return super().create(**kwargs)

    def get_with_details(self, review_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT r.*, 
                   b.title as book_title,
                   CONCAT(rd.first_name, ' ', rd.last_name) as reader_name
            FROM reviews r
            JOIN books b ON r.book_id = b.book_id
            JOIN readers rd ON r.reader_id = rd.reader_id
            WHERE r.review_id = %s
        """
        return execute_query(query, (review_id,), fetch_one=True)

    def get_by_reader(self, reader_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
            SELECT r.*, b.title as book_title
            FROM reviews r
            JOIN books b ON r.book_id = b.book_id
            WHERE r.reader_id = %s
            ORDER BY r.review_date DESC
            LIMIT %s OFFSET %s
        """
        return execute_query(query, (reader_id, limit, skip))

    def get_by_book(self, book_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
            SELECT r.*, CONCAT(rd.first_name, ' ', rd.last_name) as reader_name
            FROM reviews r
            JOIN readers rd ON r.reader_id = rd.reader_id
            WHERE r.book_id = %s
            ORDER BY r.review_date DESC
            LIMIT %s OFFSET %s
        """
        return execute_query(query, (book_id, limit, skip))


class CRUDPublisher(CRUDBase):
    def __init__(self):
        super().__init__("publishers", "publisher_id")

    def get_with_books_count(self, publisher_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT p.*, COUNT(DISTINCT b.book_id) as books_count
            FROM publishers p
            LEFT JOIN books b ON p.publisher_id = b.publisher_id
            WHERE p.publisher_id = %s
            GROUP BY p.publisher_id
        """
        return execute_query(query, (publisher_id,), fetch_one=True)


class CRUDSeries(CRUDBase):
    def __init__(self):
        super().__init__("series", "series_id")

    def get_books(self, series_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM books
            WHERE series_id = %s
            ORDER BY series_number, publication_year
        """
        return execute_query(query, (series_id,))


crud_book = CRUDBook()
crud_author = CRUDAuthor()
crud_genre = CRUDGenre()
crud_publisher = CRUDPublisher()
crud_series = CRUDSeries()
crud_reader = CRUDReader()
crud_review = CRUDReview()