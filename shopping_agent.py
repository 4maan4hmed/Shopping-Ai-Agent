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
@tool
def product_checkout(product_id: int):
    """Simulates a checkout process for a given product id and quantity.
    Returns a JSON object with the following fields: product_id, quantity, total_price, and a message confirming the purchase."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    if not result:
        return f"error : Product with id {product_id} not found."
    name = result[0]
    price = result[1]
    cursor.execute("INSERT INTO orders (product_id, product_name ,price) VALUES (?,?,?)", (product_id,name,price))
    conn.commit()   
    # Here you would normally handle payment processing and inventory management
    conn.close()
    return (f"Successfully purchased {name} for ${price:.2f}. Thank you for your purchase!",
            f"Your order will arrive in 3-5 business days.")
    
    
#Agent setup

load_dotenv()
llm = ChatGroq(model="qwen/qwen3-32b", temperature=0)
agent = create_agent(
    tools=[search_product, product_checkout, get_product_rating, get_products_ratings],
    model=llm,
    system_prompt=(
        "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
        "IMAGE SEARCH — when the user provides an image path:\n"
        "1. Call describe_product_image with the path to identify the product.\n"
        "2. Use the returned search_query and is_organic to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onwards.\n\n"
        "BROWSING — when the user describes what they want to buy:\n"
        "1. Call search_products to find matching items (apply any price/organic filters given).\n"
        "2. For each candidate, call get_rating to retrieve its average rating.\n"
        "3. Filter by the user's minimum rating if specified.\n"
        "4. Present qualifying products as a numbered list. For each item use this exact format "
        "   (plain text, no backticks, no code blocks, no bold, no italic):\n\n"
        "   #<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n\n"
        "   Add a blank line between each product entry for readability. "
        "   Always include (ID:X) so you can reference it later.\n"
        "5. If only one product qualifies, still show it in the list and ask: "
        "   'Would you like to order it? Just say yes or give me the number.'\n"
        "6. Do NOT call checkout at this stage.\n\n"
        "ORDERING — when the user confirms they want to buy (e.g. 'yes', 'sure', 'go ahead', "
        "'order number 2', 'the first one', 'get me #3'):\n"
        "1. Look at your previous message to find the (ID:X) for the chosen product "
        "   (if only one was listed and the user says 'yes', use that product's ID).\n"
        "2. Call checkout with that product_id (the number from (ID:X)).\n"
        "3. Confirm the order to the user in plain text.\n\n"
        "Never place an order unless the user explicitly confirms. "
        "Never guess a product_id — always take it from the (ID:X) in your own previous message."
    ),
)
if __name__ == "__main__":
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "number 1"
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)