"""Pydantic models for search analytics."""

from pydantic import BaseModel


class QueryRecord(BaseModel):
    """A single recorded search query."""

    query: str
    mode: str
    total_found: int
    latency_ms: float
    timestamp: str


class TopQuery(BaseModel):
    """A query with its frequency count."""

    query: str
    count: int


class ModeBreakdown(BaseModel):
    """Search count per mode."""

    mode: str
    count: int
    percentage: float


class AnalyticsSummary(BaseModel):
    """Aggregated analytics overview."""

    total_searches: int
    unique_queries: int
    avg_latency_ms: float
    top_queries: list[TopQuery]
    mode_breakdown: list[ModeBreakdown]
    recent_searches: list[QueryRecord]
    searches_over_time: dict[str, int]
