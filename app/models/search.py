"""Pydantic models for search requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    """Query parameters for search (used when binding from query string)."""

    q: str
    mode: str = Field(default="hybrid", pattern="^(hybrid|keyword|semantic)$")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchHit(BaseModel):
    """A single search result."""

    id: str
    title: str
    body: str
    author: str = ""
    source: str = ""
    pdf_url: str = ""
    score: float = 0.0
    match_type: str = ""  # "keyword", "semantic", "keyword+semantic"


class FacetValue(BaseModel):
    value: str
    count: int


class SearchResponse(BaseModel):
    """Aggregated search response."""

    query: str
    mode: str
    total_found: int
    results: list[SearchHit]
    facets: dict[str, list[FacetValue]] = {}
