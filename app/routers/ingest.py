"""Document ingestion router."""

import contextlib
import uuid

from fastapi import APIRouter, HTTPException

from app.models.document import ArxivIngestRequest, DocumentIngest, IngestResponse
from app.services import (
    arxiv_fetcher,
    embedding,
    qdrant_client,
    typesense_client,
)
from app.utils.text_processing import prepare_embedding_text

router = APIRouter(prefix="/ingest", tags=["ingestion"])


async def _index_documents(docs: list[dict]) -> int:
    """Index documents into both Typesense and Qdrant.

    Returns the number of documents successfully indexed.
    """
    if not docs:
        return 0

    # 1. Prepare texts for embedding
    texts = [prepare_embedding_text(d["title"], d["body"]) for d in docs]

    # 2. Generate embeddings in batch
    vectors = await embedding.embed_texts(texts)

    # 3. Upsert into Typesense (keyword index)
    await typesense_client.upsert_documents(docs)

    # 4. Upsert into Qdrant (vector index) — include metadata in payloads
    ids = [d["id"] for d in docs]
    payloads = [
        {
            "title": d["title"],
            "body": d["body"][:1000],  # truncate body in payload
            "author": d.get("author", ""),
            "source": d.get("source", ""),
            "pdf_url": d.get("pdf_url", ""),
        }
        for d in docs
    ]
    await qdrant_client.upsert_vectors(ids, vectors, payloads)

    return len(docs)


@router.post("/arxiv", response_model=IngestResponse)
async def ingest_arxiv(req: ArxivIngestRequest):
    """Fetch research papers from ArXiv and index them."""
    try:
        articles = await arxiv_fetcher.fetch_papers(
            query=req.query,
            limit=req.limit,
            category=req.category,
            sort_by=req.sort_by,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ArXiv fetch failed: {e}") from e

    docs = [a.model_dump() for a in articles]
    count = await _index_documents(docs)

    return IngestResponse(
        job_id=str(uuid.uuid4()),
        documents_queued=count,
        status="completed",
    )


@router.post("/documents", response_model=IngestResponse)
async def ingest_documents(req: DocumentIngest):
    """Manually ingest a list of documents."""
    docs = [d.model_dump() for d in req.documents]
    count = await _index_documents(docs)

    return IngestResponse(
        job_id=str(uuid.uuid4()),
        documents_queued=count,
        status="completed",
    )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document from both indexes."""
    with contextlib.suppress(Exception):
        await typesense_client.delete_document(doc_id)
    with contextlib.suppress(Exception):
        await qdrant_client.delete_vector(doc_id)
    return {"status": "deleted", "doc_id": doc_id}


@router.get("/documents")
async def list_documents(
    limit: int = 20,
    offset: int = 0,
):
    """Browse all ingested documents."""
    raw = await typesense_client.list_documents(limit=limit, offset=offset)
    docs = [
        {
            "id": h["document"]["id"],
            "title": h["document"].get("title", ""),
            "body": h["document"].get("body", "")[:200],
            "author": h["document"].get("author", ""),
            "source": h["document"].get("source", ""),
            "pdf_url": h["document"].get("pdf_url", ""),
        }
        for h in raw.get("hits", [])
    ]
    return {
        "documents": docs,
        "total": raw.get("found", 0),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/documents")
async def purge_all_documents():
    """Delete ALL documents from both indexes."""
    ts_count = 0
    with contextlib.suppress(Exception):
        ts_count = await typesense_client.delete_all_documents()
    with contextlib.suppress(Exception):
        await qdrant_client.delete_all_vectors()
    return {"status": "purged", "typesense_deleted": ts_count}
