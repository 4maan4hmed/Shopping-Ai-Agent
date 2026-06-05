import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage

from shopping_agent import describe_product_image, invoke_agent, product_checkout, search_product


def chat(message: str) -> Dict[str, Any]:
    result = invoke_agent([HumanMessage(content=message)])
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


def checkout(product_id: int) -> Dict[str, Any]:
    result = product_checkout.invoke({"product_id": product_id})
    if isinstance(result, tuple):
        return {"message": result[0], "details": result[1]}
    return {"message": str(result)}


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
