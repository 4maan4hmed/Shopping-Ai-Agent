"""Reviews API - reads from the 'reviews' table stored in store.db and fetches the average rating for a given product id"""

import sqlite3
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'store.db')

def get_product_rating(product_id :int):
    """Fetches the average rating for a given product id from the 'reviews' table in store.db"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()
    conn.close()
    avg = round(result[0], 2) if result[0] is not None else 0.00  # No reviews found for the given product_id
    count = result[1] if result else 0  # No reviews found for the given product_id
    return {"product_id": product_id, "average_rating": avg, "review_count": count}

def get_products_ratings(product_ids: list):
    """Fetches the average ratings for a list of product ids from the 'reviews' table in store.db"""
    if not product_ids:
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join('?'* len(product_ids))
    cursor.execute(f"SELECT product_id, AVG(rating), COUNT(*) FROM reviews WHERE product_id IN ({placeholders}) GROUP BY product_id", product_ids)
    results = cursor.fetchall()
    conn.close()
    rating_dict = {product_id: {"average_rating": round(avg, 2) if avg is not None else 0.00, "review_count": count} for product_id, avg, count in results}
    return [
        {"product_id": product_id,
         "average_rating": rating_dict.get(product_id, {}).get("average_rating", 0.00),
         "review_count": rating_dict.get(product_id, {}).get("review_count", 0)
        }
        for product_id in product_ids
    ]
