"""Embedding generation service — supports Gemini and OpenAI."""

from app.config import get_settings


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Uses Google Gemini text-embedding-004 (768 dims) by default.
    Falls back to OpenAI if configured.
    """
    s = get_settings()

    if s.llm_provider == "openai":
        return await _embed_openai(texts, s)
    return await _embed_gemini(texts, s)


async def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    vectors = await embed_texts([text])
    return vectors[0]


async def _embed_gemini(texts: list[str], s) -> list[list[float]]:
    """Generate embeddings using Gemini's OpenAI-compatible endpoint."""
    from openai import OpenAI

    client = OpenAI(
        api_key=s.gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    response = client.embeddings.create(
        input=texts,
        model=s.embedding_model,
        dimensions=s.embedding_dimensions,
    )
    return [item.embedding for item in response.data]


async def _embed_openai(texts: list[str], s) -> list[list[float]]:
    """Generate embeddings using OpenAI."""
    from openai import OpenAI

    client = OpenAI(api_key=s.openai_api_key)
    response = client.embeddings.create(
        input=texts,
        model=s.embedding_model,
        dimensions=s.embedding_dimensions,
    )
    return [item.embedding for item in response.data]
