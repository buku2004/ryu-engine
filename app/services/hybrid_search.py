"""Hybrid search — Reciprocal Rank Fusion of keyword + vector results."""

from app.config import get_settings
from app.models.search import SearchHit
from app.services import embedding, qdrant_client, typesense_client
from app.services.arxiv_fetcher import build_pdf_url, extract_arxiv_id_from_body


def _resolve_pdf_url(doc: dict) -> str:
    """Return a PDF URL for ArXiv documents, including older indexed docs."""
    pdf_url = doc.get("pdf_url", "")
    if pdf_url:
        return pdf_url
    if doc.get("source") != "arxiv":
        return ""
    arxiv_id = extract_arxiv_id_from_body(doc.get("body", ""))
    if not arxiv_id:
        return ""
    return build_pdf_url(arxiv_id)


async def hybrid_search(
    query: str, limit: int = 10, offset: int = 0
) -> tuple[list[SearchHit], int]:
    """Execute hybrid search and return fused results.

    1. Run keyword search (Typesense) and vector search (Qdrant) concurrently.
    2. Merge using Reciprocal Rank Fusion.
    3. Return deduplicated, re-ranked results.
    """
    import asyncio

    # Run both searches concurrently
    query_vector = await embedding.embed_query(query)
    keyword_task = asyncio.create_task(
        typesense_client.search(query, limit=limit * 2)
    )
    vector_task = asyncio.create_task(
        qdrant_client.search(query_vector, limit=limit * 2)
    )

    keyword_results, vector_results = await asyncio.gather(
        keyword_task, vector_task
    )

    # Parse keyword results into a uniform shape
    keyword_hits: list[dict] = []
    for hit in keyword_results.get("hits", []):
        doc = hit["document"]
        keyword_hits.append(
            {
                "id": doc["id"],
                "title": doc.get("title", ""),
                "body": doc.get("body", ""),
                "author": doc.get("author", ""),
                "source": doc.get("source", ""),
                "pdf_url": _resolve_pdf_url(doc),
            }
        )

    # Parse vector results (already normalised by the qdrant service)
    vector_hits: list[dict] = []
    for hit in vector_results:
        vector_hits.append(
            {
                "id": hit["doc_id"],
                "title": hit.get("title", ""),
                "body": hit.get("body", ""),
                "author": hit.get("author", ""),
                "source": hit.get("source", ""),
                "pdf_url": _resolve_pdf_url(hit),
            }
        )

    # ---- Reciprocal Rank Fusion ----
    s = get_settings()
    k = s.hybrid_k  # default 60
    scores: dict[str, float] = {}
    docs_by_id: dict[str, dict] = {}
    match_types: dict[str, set[str]] = {}

    for rank, hit in enumerate(keyword_hits):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs_by_id[doc_id] = hit
        match_types.setdefault(doc_id, set()).add("keyword")

    for rank, hit in enumerate(vector_hits):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs_by_id[doc_id] = hit
        match_types.setdefault(doc_id, set()).add("semantic")

    # Sort by fused score descending
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

    # Apply offset + limit
    page_ids = sorted_ids[offset : offset + limit]

    results: list[SearchHit] = []
    for doc_id in page_ids:
        doc = docs_by_id[doc_id]
        mt = "+".join(sorted(match_types[doc_id]))
        results.append(
            SearchHit(
                id=doc_id,
                title=doc["title"],
                body=doc["body"],
                author=doc.get("author", ""),
                source=doc.get("source", ""),
                pdf_url=doc.get("pdf_url", ""),
                score=round(scores[doc_id], 4),
                match_type=mt,
            )
        )

    return results, len(sorted_ids)


async def keyword_only(
    query: str, limit: int = 10, offset: int = 0
) -> tuple[list[SearchHit], int]:
    """Keyword-only search via Typesense."""
    raw = await typesense_client.search(query, limit=limit, offset=offset)
    results = [
        SearchHit(
            id=h["document"]["id"],
            title=h["document"].get("title", ""),
            body=h["document"].get("body", ""),
            author=h["document"].get("author", ""),
            source=h["document"].get("source", ""),
            pdf_url=_resolve_pdf_url(h["document"]),
            score=h.get("text_match_info", {}).get("score", 0),
            match_type="keyword",
        )
        for h in raw.get("hits", [])
    ]
    return results, raw.get("found", 0)


async def semantic_only(
    query: str, limit: int = 10
) -> tuple[list[SearchHit], int]:
    """Semantic-only search via Qdrant."""
    query_vector = await embedding.embed_query(query)
    raw = await qdrant_client.search(query_vector, limit=limit)
    results = [
        SearchHit(
            id=h["doc_id"],
            title=h.get("title", ""),
            body=h.get("body", ""),
            author=h.get("author", ""),
            source=h.get("source", ""),
            pdf_url=_resolve_pdf_url(h),
            score=round(h["score"], 4),
            match_type="semantic",
        )
        for h in raw
    ]
    return results, len(results)
