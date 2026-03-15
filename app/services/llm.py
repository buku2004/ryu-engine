"""LLM service — GPT-4 / Gemini for RAG summarisation."""

import asyncio
import logging

from openai import OpenAI

from app.config import get_settings

log = logging.getLogger(__name__)

_openai_client: OpenAI | None = None
_gemini_client: OpenAI | None = None

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2  # seconds

SYSTEM_PROMPT = """You are Ryu, an AI search assistant specialising in topic-specific knowledge.
You answer questions based ONLY on the provided context documents.
If the context does not contain enough information, say so honestly.
Always cite which source documents support your answer.
Keep answers clear, concise, and well-structured."""

SUMMARY_PROMPT = """You are Ryu, an AI assistant that creates concise summaries.
Summarize the following document clearly and accurately.
Highlight the key points, main arguments, and any conclusions.
Keep the summary to 3-5 sentences unless the content is very long.
Do not add information that is not in the original text."""


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        s = get_settings()
        _openai_client = OpenAI(api_key=s.openai_api_key)
    return _openai_client


def _get_gemini_client() -> OpenAI:
    global _gemini_client
    if _gemini_client is None:
        s = get_settings()
        _gemini_client = OpenAI(
            api_key=s.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return _gemini_client


def _build_context(sources: list[dict]) -> str:
    """Format search results into a context block for the LLM."""
    parts: list[str] = []
    for i, src in enumerate(sources, 1):
        parts.append(
            f"[Source {i}] Title: {src.get('title', 'N/A')}\n"
            f"Author: {src.get('author', 'N/A')}\n"
            f"Content: {src.get('body', '')[:1500]}\n"
        )
    return "\n---\n".join(parts)


async def generate_answer(
    question: str,
    sources: list[dict],
    history: list[dict] | None = None,
) -> str:
    """Generate an LLM answer grounded in search-result context."""
    s = get_settings()
    context = _build_context(sources)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Append prior conversation turns if available
    if history:
        messages.extend(history)

    user_content = (
        f"Context documents:\n{context}\n\n"
        f"User question: {question}\n\n"
        "Answer the question using ONLY the context above. "
        "Cite sources by their [Source N] number."
    )
    messages.append({"role": "user", "content": user_content})

    if s.llm_provider == "gemini":
        return await _call_gemini(messages, s)

    return await _call_openai(messages, s)


async def generate_summary(title: str, body: str, max_chars: int = 4000) -> str:
    """Generate a concise summary of a document using the LLM."""
    s = get_settings()
    content = f"Title: {title}\n\nContent:\n{body[:max_chars]}"
    messages = [
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": content},
    ]
    if s.llm_provider == "gemini":
        return await _call_gemini(messages, s)
    return await _call_openai(messages, s)


async def _call_openai(messages: list[dict], s) -> str:
    """Call OpenAI chat completion (sync SDK, offloaded to thread)."""
    def _sync_call() -> str:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=s.openai_chat_model,
            messages=messages, # type: ignore
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    try:
        return await asyncio.to_thread(_sync_call)
    except Exception as e:
        log.error("OpenAI call failed: %s", e)
        raise


async def _call_gemini(messages: list[dict], s) -> str:
    """Call Gemini via Google's OpenAI-compatible endpoint with retry."""
    client = _get_gemini_client()

    def _sync_call() -> str:
        response = client.chat.completions.create(
            model=s.gemini_model,
            messages=messages, # type: ignore
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return await asyncio.to_thread(_sync_call)
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            is_retryable = "429" in str(e) or "quota" in err_str or "rate" in err_str or "resource" in err_str
            if is_retryable and attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                log.warning("Gemini rate-limited (attempt %d/%d), retrying in %ds: %s",
                            attempt + 1, _MAX_RETRIES, delay, e)
                await asyncio.sleep(delay)
            else:
                log.error("Gemini call failed: %s", e)
                raise

    raise RuntimeError("Gemini call failed after all retries") from last_err
