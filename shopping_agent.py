import json
import sqlite3
from typing import Optional
import os 
from dotenv import load_dotenv
from reviews_api import DB_PATH, get_product_rating, get_products_ratings
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

@tool
def search_product (query: str, max_price : Optional[float] = None, is_organic : Optional[bool]= None):
    """Searches for products database by keyword(matched against product names, descriptions and category ).
    Optional filters by max_price and is_organic,
    returns a JSON list of matching products with the following fields: id, name, description, price, is_organic, category"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql_query = "SELECT id, name, description, price, is_organic, category FROM products WHERE 1=1"
    params : list = [] 
    if query:
        sql_query += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like_query = f"%{query}%"
        params.extend([like_query, like_query, like_query])
    if max_price is not None:
        sql_query += " AND price <= ?"
        params.append(max_price)
    if is_organic is not None:
        sql_query += " AND is_organic = ?"
        params.append(1 if is_organic else 0)
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    conn.close()
    products = [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3],
            "is_organic": bool(row[4]),
            "category": row[5]
        }
        for row in rows
    ]
    return json.dumps(products)
print(search_product("honey", max_price=10.0, is_organic=True))