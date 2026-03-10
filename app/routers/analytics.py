"""Analytics router — search usage metrics and dashboard data."""

from fastapi import APIRouter

from app.models.analytics import AnalyticsSummary
from app.services.analytics import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummary)
async def get_analytics():
    """Return aggregated search analytics."""
    return analytics.get_summary()
