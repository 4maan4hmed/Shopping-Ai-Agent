import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage

from services.auth_service import get_connection
from shopping_agent import describe_product_image, invoke_agent, product_checkout, search_product


def chat(message: str, user_id: int) -> Dict[str, Any]:
    content = f"Authenticated user_id for checkout: {user_id}\n\nUser message: {message}"
    result = invoke_agent([HumanMessage(content=content)])
    last = result["messages"][-1]
    reply = last.content if hasattr(last, "content") else str(last)
    return {"reply": reply, "messages": [msg.content for msg in result["messages"]]}


def search_products(query: str, max_price: Optional[float] = None, is_organic: Optional[bool] = None) -> Dict[str, Any]:
    raw = search_product.invoke({
        "query": query,
        "max_price": max_price,
        "is_organic": is_organic,
    })
    return {"products": json.loads(raw)}


def get_cart(user_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                ci.product_id,
                ci.quantity,
                p.name,
                p.description,
                p.price,
                p.is_organic,
                p.category
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            ORDER BY ci.updated_at DESC
            """,
            (user_id,),
        ).fetchall()

    items = [
        {
            "product_id": row["product_id"],
            "quantity": row["quantity"],
            "name": row["name"],
            "description": row["description"],
            "price": row["price"],
            "is_organic": bool(row["is_organic"]),
            "category": row["category"],
            "line_total": round(row["price"] * row["quantity"], 2),
        }
        for row in rows
    ]
    return {"items": items, "total": round(sum(item["line_total"] for item in items), 2)}


def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> Dict[str, Any]:
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")

    with get_connection() as conn:
        product = conn.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            raise ValueError(f"Product with id {product_id} not found")

        conn.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id) DO UPDATE SET
                quantity = quantity + excluded.quantity,
                updated_at = datetime('now')
            """,
            (user_id, product_id, quantity),
        )

    return get_cart(user_id)


def remove_from_cart(user_id: int, product_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        conn.execute("DELETE FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    return get_cart(user_id)


def clear_cart(user_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    return get_cart(user_id)


def checkout(product_id: int, user_id: int) -> Dict[str, Any]:
    result = product_checkout.invoke({"product_id": product_id, "user_id": user_id})
    if not (isinstance(result, str) and result.startswith("error")):
        with get_connection() as conn:
            conn.execute("DELETE FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    if isinstance(result, tuple):
        return {"message": result[0], "details": result[1]}
    return {"message": str(result)}


def get_deliveries(user_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, product_id, product_name, price, ordered_at
            FROM orders
            WHERE user_id = ?
            ORDER BY ordered_at DESC
            """,
            (user_id,),
        ).fetchall()

    return {
        "deliveries": [
            {
                "order_id": row["id"],
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "price": row["price"],
                "ordered_at": row["ordered_at"],
                "status": "preparing",
                "estimate": "3-5 business days",
            }
            for row in rows
        ]
    }


def image_search(file_obj, filename: str, caption: str = "") -> Dict[str, Any]:
    temp_path = None
    try:
        suffix = Path(filename or "image.jpg").suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file_obj, tmp)
            temp_path = tmp.name

        analysis = describe_product_image.invoke({"image_path": temp_path})
        parsed = json.loads(analysis) if isinstance(analysis, str) else analysis

        if caption:
            parsed["caption"] = caption

        query = str(parsed.get("search_query") or "").strip() or (caption or "product")
        products = search_products(query)

        return {"analysis": parsed, "products": products["products"]}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
