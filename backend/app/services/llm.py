"""LLM service — GPT-4 / Gemini for RAG summarisation."""

from openai import OpenAI
from app.config import get_settings

_openai_client: OpenAI | None = None

SYSTEM_PROMPT = """You are Ryu, an AI search assistant specialising in topic-specific knowledge.
You answer questions based ONLY on the provided context documents.
If the context does not contain enough information, say so honestly.
Always cite which source documents support your answer.
Keep answers clear, concise, and well-structured."""


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        s = get_settings()
        _openai_client = OpenAI(api_key=s.openai_api_key)
    return _openai_client


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
    """Generate an LLM answer grounded in search-result context.

    Supports OpenAI (GPT-4) as primary, with Gemini as a future option.
    """
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


async def _call_openai(messages: list[dict], s) -> str:
    """Call OpenAI chat completion."""
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=s.openai_chat_model,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


async def _call_gemini(messages: list[dict], s) -> str:
    """Call Gemini via Google's OpenAI-compatible endpoint."""
    from openai import OpenAI as GeminiClient

    client = GeminiClient(
        api_key=s.gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    response = client.chat.completions.create(
        model=s.gemini_model,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""
