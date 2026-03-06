"""Ryu Engine — FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, ingest, search, chat
from app.services import typesense_client, qdrant_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Ensure collections exist on startup
    await typesense_client.ensure_collection()
    await qdrant_client.ensure_collection()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered topic-specific hybrid search engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }
