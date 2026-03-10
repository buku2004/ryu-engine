"""Search router — hybrid, keyword-only, and semantic-only endpoints."""

import time
from fastapi import APIRouter, Query
from app.services.hybrid_search import hybrid_search, keyword_only, semantic_only
from app.services.analytics import analytics
from app.models.search import SearchResponse, SearchHit

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    mode: str = Query("hybrid", pattern="^(hybrid|keyword|semantic)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Run a hybrid, keyword, or semantic search."""
    start = time.perf_counter()

    if mode == "keyword":
        results, total = await keyword_only(q, limit=limit, offset=offset)
    elif mode == "semantic":
        results, total = await semantic_only(q, limit=limit)
    else:
        results, total = await hybrid_search(q, limit=limit, offset=offset)

    latency_ms = (time.perf_counter() - start) * 1000
    analytics.record(query=q, mode=mode, total_found=total, latency_ms=latency_ms)

    return SearchResponse(
        query=q,
        mode=mode,
        total_found=total,
        results=results,
    )


@router.get("/keyword", response_model=SearchResponse)
async def search_keyword(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Keyword-only search via Typesense."""
    results, total = await keyword_only(q, limit=limit, offset=offset)
    return SearchResponse(
        query=q, mode="keyword", total_found=total, results=results
    )


@router.get("/semantic", response_model=SearchResponse)
async def search_semantic(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Semantic-only search via Qdrant."""
    results, total = await semantic_only(q, limit=limit)
    return SearchResponse(
        query=q, mode="semantic", total_found=total, results=results
    )
