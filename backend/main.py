"""FastAPI application entry point.

Run locally:
    uvicorn backend.main:app --reload

All routers are registered here. Add new routers via app.include_router().
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.router import router as auth_router
from backend.billing.router import router as billing_router
from backend.routers.files import router as files_router
from backend.routers.profiles import router as profiles_router
from backend.routers.reports import router as reports_router
from backend.routers.sessions import router as sessions_router
from backend.websocket.session_handler import router as ws_router

app = FastAPI(
    title="Interview Platform API",
    description="Real-time interview intelligence platform backend.",
    version="0.1.0",
)

_raw_origins = os.getenv("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# allow_credentials=True requires explicit origins (not wildcard)
_allow_credentials = bool(_cors_origins)
if not _cors_origins:
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(profiles_router)
app.include_router(sessions_router)
app.include_router(files_router)
app.include_router(reports_router)
app.include_router(ws_router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
