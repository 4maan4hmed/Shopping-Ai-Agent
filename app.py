from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.shopping_service import chat, checkout, image_search, search_products


class ChatRequest(BaseModel):
    message: str


class SearchRequest(BaseModel):
    query: str
    max_price: Optional[float] = None
    is_organic: Optional[bool] = None


class CheckoutRequest(BaseModel):
    product_id: int


app = FastAPI(title="Shopping AI Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "shopping-ai-agent"}


@app.get("/")
async def root() -> dict:
    return {
        "message": "Shopping AI Agent FastAPI backend is running.",
        "endpoints": ["/health", "/api/chat", "/api/products/search", "/api/checkout"],
    }


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> dict:
    try:
        return chat(request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/products/search")
async def search_products_endpoint(request: SearchRequest) -> dict:
    try:
        return search_products(request.query, request.max_price, request.is_organic)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/checkout")
async def checkout_endpoint(request: CheckoutRequest) -> dict:
    try:
        return checkout(request.product_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/image-search")
async def image_search_endpoint(image: UploadFile = File(...), caption: str = "") -> dict:
    try:
        return image_search(image.file, image.filename or "image.jpg", caption)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
