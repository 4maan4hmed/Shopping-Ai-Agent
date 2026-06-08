import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from reviews_api import DB_PATH


JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "1440"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """
        )

        order_columns = {row["name"] for row in conn.execute("PRAGMA table_info(orders)")}
        if "user_id" not in order_columns:
            conn.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id)")


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    actual = _hash_password(password, salt)
    return hmac.compare_digest(actual, f"{algorithm}${salt}${expected}")


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-shopping-agent-secret")


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str) -> str:
    digest = hmac.new(_jwt_secret().encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def create_access_token(user: sqlite3.Row) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRY_MINUTES)).timestamp()),
    }
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    return f"{signing_input}.{_sign(signing_input)}"


def verify_access_token(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}"
        if not hmac.compare_digest(signature, _sign(signing_input)):
            raise ValueError("Invalid token signature")

        header = json.loads(_base64url_decode(header_b64))
        payload = json.loads(_base64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError, binascii.Error) as exc:
        raise ValueError("Invalid token") from exc

    if header.get("alg") != JWT_ALGORITHM:
        raise ValueError("Invalid token algorithm")

    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token has expired")

    return payload


def register_user(username: str, password: str) -> Dict[str, Any]:
    username = username.strip()
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, _hash_password(password)),
            )
            user = conn.execute("SELECT id, username FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError as exc:
        raise ValueError("Username already exists") from exc

    return _auth_response(user)


def login_user(username: str, password: str) -> Dict[str, Any]:
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    if user is None or not _verify_password(password, user["password_hash"]):
        raise ValueError("Invalid username or password")

    return _auth_response(user)


def get_user_by_id(user_id: int) -> Dict[str, Any] | None:
    with get_connection() as conn:
        user = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(user) if user else None


def _auth_response(user: sqlite3.Row) -> Dict[str, Any]:
    public_user = {"id": user["id"], "username": user["username"]}
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": public_user,
    }
