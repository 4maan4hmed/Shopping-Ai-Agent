"""Reviews API - reads from the 'reviews' table stored in store.db and fetches the average reviews for a given product id"""

import sqlite3
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'store.db')

def get_average_review(product_id):
    """Fetches the average review for a given product id from the 'reviews' table in store.db"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()
    avg = round(result[0], 2) if result[0] is not None else 0.00  # No reviews found for the given product_id
    count = result[1] if result else 0  # No reviews found for the given product_id
    return {"product_id": product_id, "average_rating": avg, "review_count": count}