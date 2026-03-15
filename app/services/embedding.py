"""Embedding generation service — supports Gemini and OpenAI."""

import asyncio

from openai import OpenAI

from app.config import get_settings

_gemini_embed_client: OpenAI | None = None
_openai_embed_client: OpenAI | None = None


def _get_gemini_embed_client() -> OpenAI:
    global _gemini_embed_client
    if _gemini_embed_client is None:
        s = get_settings()
        _gemini_embed_client = OpenAI(
            api_key=s.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return _gemini_embed_client


def _get_openai_embed_client() -> OpenAI:
    global _openai_embed_client
    if _openai_embed_client is None:
        s = get_settings()
        _openai_embed_client = OpenAI(api_key=s.openai_api_key)
    return _openai_embed_client


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
    client = _get_gemini_embed_client()

    def _sync_call() -> list[list[float]]:
        response = client.embeddings.create(
            input=texts,
            model=s.embedding_model,
            dimensions=s.embedding_dimensions,
        )
        return [item.embedding for item in response.data]

    return await asyncio.to_thread(_sync_call)


async def _embed_openai(texts: list[str], s) -> list[list[float]]:
    """Generate embeddings using OpenAI."""
    client = _get_openai_embed_client()

    def _sync_call() -> list[list[float]]:
        response = client.embeddings.create(
            input=texts,
            model=s.embedding_model,
            dimensions=s.embedding_dimensions,
        )
        return [item.embedding for item in response.data]

    return await asyncio.to_thread(_sync_call)
