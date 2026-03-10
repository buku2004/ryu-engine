"""Typesense client — collection management and search operations."""

import typesense
from app.config import get_settings

_client: typesense.Client | None = None


def get_client() -> typesense.Client:
    """Return a lazily-initialised Typesense client."""
    global _client
    if _client is None:
        s = get_settings()
        _client = typesense.Client(
            {
                "nodes": [
                    {
                        "host": s.typesense_host,
                        "port": str(s.typesense_port),
                        "protocol": s.typesense_protocol,
                    }
                ],
                "api_key": s.typesense_api_key,
                "connection_timeout_seconds": 5,
            }
        )
    return _client


COLLECTION_SCHEMA = {
    "name": "",  # filled at runtime
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "body", "type": "string"},
        {"name": "author", "type": "string", "facet": True},
        {"name": "created_at", "type": "int64", "facet": True},
        {"name": "source", "type": "string", "facet": True},
    ],
}


async def ensure_collection() -> None:
    """Create the collection if it doesn't already exist."""
    s = get_settings()
    client = get_client()
    try:
        client.collections[s.typesense_collection].retrieve()
    except typesense.exceptions.ObjectNotFound:
        schema = {**COLLECTION_SCHEMA, "name": s.typesense_collection}
        client.collections.create(schema)


async def upsert_documents(docs: list[dict]) -> dict:
    """Upsert documents into Typesense using JSONL import."""
    s = get_settings()
    client = get_client()
    return client.collections[s.typesense_collection].documents.import_(
        docs, {"action": "upsert"}
    )


async def search(query: str, limit: int = 10, offset: int = 0) -> dict:
    """Run a keyword search against Typesense."""
    s = get_settings()
    client = get_client()
    params = {
        "q": query,
        "query_by": "title,body",
        "per_page": limit,
        "page": (offset // limit) + 1,
        "facet_by": "source,author",
    }
    return client.collections[s.typesense_collection].documents.search(params)


async def delete_document(doc_id: str) -> None:
    """Delete a single document by ID."""
    s = get_settings()
    client = get_client()
    client.collections[s.typesense_collection].documents[doc_id].delete()


async def list_documents(limit: int = 20, offset: int = 0) -> dict:
    """List all documents using a wildcard search."""
    s = get_settings()
    client = get_client()
    params = {
        "q": "*",
        "query_by": "title",
        "per_page": limit,
        "page": (offset // limit) + 1,
        "sort_by": "created_at:desc",
    }
    return client.collections[s.typesense_collection].documents.search(params)


async def delete_all_documents() -> int:
    """Delete all documents in the collection. Returns count deleted."""
    s = get_settings()
    client = get_client()
    result = client.collections[s.typesense_collection].documents.delete(
        {"filter_by": "source:!=[]"}  # matches all docs
    )
    return result.get("num_deleted", 0)


async def health_check() -> bool:
    """Return True if Typesense is reachable."""
    try:
        client = get_client()
        client.operations.is_healthy()
        return True
    except Exception:
        return False
