"""Qdrant client — vector collection management and search."""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    SearchParams,
)
from app.config import get_settings

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    """Return a lazily-initialised Qdrant client."""
    global _client
    if _client is None:
        s = get_settings()
        _client = QdrantClient(host=s.qdrant_host, port=s.qdrant_port)
    return _client


async def ensure_collection() -> None:
    """Create the vector collection if it doesn't exist."""
    s = get_settings()
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if s.qdrant_collection not in collections:
        client.create_collection(
            collection_name=s.qdrant_collection,
            vectors_config=VectorParams(
                size=s.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )


async def upsert_vectors(
    ids: list[str],
    vectors: list[list[float]],
    payloads: list[dict],
) -> None:
    """Upsert vectors with payloads into Qdrant."""
    s = get_settings()
    client = get_client()
    points = [
        PointStruct(id=idx, vector=vec, payload=pay)
        for idx, vec, pay in zip(range(len(ids)), vectors, payloads)
    ]
    # Store string IDs in the payload so we can map back
    for i, point in enumerate(points):
        point.payload["doc_id"] = ids[i]

    client.upsert(collection_name=s.qdrant_collection, points=points)


async def search(
    query_vector: list[float],
    limit: int = 10,
) -> list[dict]:
    """Search for nearest neighbours and return results with scores."""
    s = get_settings()
    client = get_client()
    results = client.search(
        collection_name=s.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
    )
    return [
        {
            "doc_id": hit.payload.get("doc_id", ""),
            "title": hit.payload.get("title", ""),
            "body": hit.payload.get("body", ""),
            "author": hit.payload.get("author", ""),
            "source": hit.payload.get("source", ""),
            "pdf_url": hit.payload.get("pdf_url", ""),
            "score": hit.score,
        }
        for hit in results
    ]


async def delete_vector(doc_id: str) -> None:
    """Delete vectors matching a doc_id payload filter."""
    from qdrant_client.models import FieldCondition, MatchValue

    s = get_settings()
    client = get_client()
    client.delete(
        collection_name=s.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )


async def delete_all_vectors() -> None:
    """Delete and recreate the collection to purge all vectors."""
    s = get_settings()
    client = get_client()
    client.delete_collection(collection_name=s.qdrant_collection)
    client.create_collection(
        collection_name=s.qdrant_collection,
        vectors_config=VectorParams(
            size=s.embedding_dimensions,
            distance=Distance.COSINE,
        ),
    )


async def health_check() -> bool:
    """Return True if Qdrant is reachable."""
    try:
        client = get_client()
        client.get_collections()
        return True
    except Exception:
        return False
