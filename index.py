"""Vercel ASGI entrypoint. Existing backend routes remain available under /api."""
from fastapi import FastAPI
from backend.app.main import app as api

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, debug=False)
app.mount("/api", api)
app.frontend("/", directory="dist", fallback="index.html", check_dir=False)
