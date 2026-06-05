import os

import uvicorn


def main() -> None:
    reload = os.getenv("UVICORN_RELOAD", "false").lower() in {"1", "true", "yes", "on"}
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=reload)


if __name__ == "__main__":
    main()
