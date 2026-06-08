from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from services.auth_service import get_user_by_id, init_auth_db, login_user, register_user, verify_access_token
from services.shopping_service import (
    add_to_cart,
    chat,
    checkout,
    clear_cart,
    get_cart,
    get_deliveries,
    image_search,
    remove_from_cart,
    search_products,
)


class ChatRequest(BaseModel):
    message: str


class AuthRequest(BaseModel):
    username: str
    password: str


class SearchRequest(BaseModel):
    query: str
    max_price: Optional[float] = None
    is_organic: Optional[bool] = None


class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = 1


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
security = HTTPBearer()
init_auth_db()


def current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = verify_access_token(credentials.credentials)
        user = get_user_by_id(int(payload["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "shopping-ai-agent"}


@app.get("/")
async def root() -> dict:
    return {
        "message": "Shopping AI Agent FastAPI backend is running.",
        "endpoints": [
            "/health",
            "/api/auth/register",
            "/api/auth/login",
            "/api/chat",
            "/api/products/search",
            "/api/cart",
            "/api/checkout",
            "/api/deliveries",
        ],
    }


@app.post("/api/auth/register")
async def register_endpoint(request: AuthRequest) -> dict:
    try:
        return register_user(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/api/auth/login")
async def login_endpoint(request: AuthRequest) -> dict:
    try:
        return login_user(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/api/auth/me")
async def me_endpoint(user: dict = Depends(current_user)) -> dict:
    return {"user": user}


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, user: dict = Depends(current_user)) -> dict:
    try:
        return chat(request.message, user["id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/products/search")
async def search_products_endpoint(request: SearchRequest) -> dict:
    try:
        return search_products(request.query, request.max_price, request.is_organic)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/cart")
async def get_cart_endpoint(user: dict = Depends(current_user)) -> dict:
    return get_cart(user["id"])


@app.post("/api/cart/items")
async def add_to_cart_endpoint(request: CartItemRequest, user: dict = Depends(current_user)) -> dict:
    try:
        return add_to_cart(user["id"], request.product_id, request.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.delete("/api/cart/items/{product_id}")
async def remove_from_cart_endpoint(product_id: int, user: dict = Depends(current_user)) -> dict:
    return remove_from_cart(user["id"], product_id)


@app.delete("/api/cart")
async def clear_cart_endpoint(user: dict = Depends(current_user)) -> dict:
    return clear_cart(user["id"])


@app.post("/api/checkout")
async def checkout_endpoint(request: CheckoutRequest, user: dict = Depends(current_user)) -> dict:
    try:
        return checkout(request.product_id, user["id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/deliveries")
async def deliveries_endpoint(user: dict = Depends(current_user)) -> dict:
    return get_deliveries(user["id"])


@app.post("/api/image-search")
async def image_search_endpoint(image: UploadFile = File(...), caption: str = "") -> dict:
    try:
        return image_search(image.file, image.filename or "image.jpg", caption)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
