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