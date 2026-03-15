"""Ryu Engine — FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import analytics, health, ingest, search, summarize
from app.services import qdrant_client, typesense_client

log = logging.getLogger(__name__)


async def _wait_for_dependencies(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    """Wait for search backends to become reachable during container startup."""
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            await typesense_client.ensure_collection()
            await qdrant_client.ensure_collection()
            if attempt > 1:
                log.info("Search services became ready on attempt %s", attempt)
            return
        except Exception as exc:
            last_error = exc
            log.warning(
                "Search services not ready yet (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )
            if attempt < max_attempts:
                await asyncio.sleep(delay_seconds)

    raise RuntimeError("Startup failed while waiting for Typesense/Qdrant") from last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await _wait_for_dependencies()
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
app.include_router(analytics.router)
app.include_router(summarize.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }
