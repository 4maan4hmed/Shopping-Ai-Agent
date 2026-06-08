# Shopping AI Agent

This project now runs as a FastAPI backend.

## Run the backend

```bash
"d:/Projects/Interview/Shopping Ai Agent/.venv/Scripts/python.exe" main.py
```

The API will be available at:
- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/docs

## Example requests

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "amaan", "password": "secret123"}'
```

Use the returned `access_token` as a bearer token for user-specific routes:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"message": "Find organic fruits under $4"}'
```

Simple user-specific shopping routes:

```bash
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
GET    /api/cart
POST   /api/cart/items
DELETE /api/cart/items/{product_id}
DELETE /api/cart
POST   /api/checkout
GET    /api/deliveries
```

## LangSmith setup

Add these variables to your environment before running the app:

```bash
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=shopping-ai-agent
```

With those values set, each shopping-agent run will be traceable in LangSmith.
