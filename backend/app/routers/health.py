"""Health-check router."""

from fastapi import APIRouter
from app.services import typesense_client, qdrant_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def liveness():
    """Basic liveness probe."""
    return {"status": "ok"}


@router.get("/services")
async def service_status():
    """Check connectivity to Typesense and Qdrant."""
    ts_ok = await typesense_client.health_check()
    qd_ok = await qdrant_client.health_check()
    return {
        "typesense": "connected" if ts_ok else "unreachable",
        "qdrant": "connected" if qd_ok else "unreachable",
        "all_healthy": ts_ok and qd_ok,
    }
