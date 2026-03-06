"""Document ingestion router."""

import uuid
from fastapi import APIRouter, HTTPException
from app.models.document import RedditIngestRequest, DocumentIngest, IngestResponse
from app.services import (
    reddit_fetcher,
    typesense_client,
    qdrant_client,
    embedding,
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
        }
        for d in docs
    ]
    await qdrant_client.upsert_vectors(ids, vectors, payloads)

    return len(docs)


@router.post("/reddit", response_model=IngestResponse)
async def ingest_reddit(req: RedditIngestRequest):
    """Fetch posts from a subreddit and index them."""
    try:
        posts = await reddit_fetcher.fetch_posts(
            subreddit=req.subreddit,
            limit=req.limit,
            sort=req.sort,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reddit fetch failed: {e}")

    docs = [p.model_dump() for p in posts]
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
    try:
        await typesense_client.delete_document(doc_id)
    except Exception:
        pass  # may not exist in Typesense
    try:
        await qdrant_client.delete_vector(doc_id)
    except Exception:
        pass
    return {"status": "deleted", "doc_id": doc_id}
