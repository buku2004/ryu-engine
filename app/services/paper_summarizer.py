"""On-demand ArXiv PDF summarization with in-memory caching and rate limits."""

from __future__ import annotations

import io
import time
from collections import deque

import httpx
from pypdf import PdfReader  # pyright: ignore[reportMissingImports]

from app.config import get_settings
from app.services.arxiv_fetcher import build_pdf_url, extract_arxiv_id_from_body
from app.services.llm import generate_summary

# In-memory cache: doc_id -> {summary: str, expires_at: float}
_summary_cache: dict[str, dict[str, float | str]] = {}

# Global limiter timestamps (seconds since epoch)
_call_timestamps: deque[float] = deque()


class PdfSummaryError(Exception):
    """Raised when PDF summarization cannot be completed."""


class PdfSummaryRateLimitError(Exception):
    """Raised when the in-memory rate limiter blocks the request."""


def _extract_arxiv_id(body: str) -> str:
    arxiv_id = extract_arxiv_id_from_body(body)
    if not arxiv_id:
        raise PdfSummaryError("No ArXiv ID found for this document.")
    return arxiv_id


def _prune_rate_window(now: float) -> None:
    window_start = now - 3600
    while _call_timestamps and _call_timestamps[0] < window_start:
        _call_timestamps.popleft()


def _enforce_rate_limit() -> None:
    settings = get_settings()
    now = time.time()
    _prune_rate_window(now)
    if len(_call_timestamps) >= settings.pdf_summary_max_calls_per_hour:
        raise PdfSummaryRateLimitError(
            "Full-paper summary quota reached. Try again later or use regular summary."
        )
    _call_timestamps.append(now)


def _get_cached_summary(doc_id: str) -> str | None:
    now = time.time()
    entry = _summary_cache.get(doc_id)
    if not entry:
        return None
    expires_at = float(entry.get("expires_at", 0))
    if expires_at <= now:
        _summary_cache.pop(doc_id, None)
        return None
    summary = entry.get("summary")
    if isinstance(summary, str):
        return summary
    return None


def _set_cached_summary(doc_id: str, summary: str) -> None:
    settings = get_settings()
    _summary_cache[doc_id] = {
        "summary": summary,
        "expires_at": time.time() + settings.pdf_summary_cache_ttl_sec,
    }


def _extract_text_sections(pdf_bytes: bytes, max_chars: int) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise PdfSummaryError("The PDF appears to have no pages.")

    first_page_count = min(6, total_pages)
    front_text_parts: list[str] = []
    for idx in range(first_page_count):
        txt = reader.pages[idx].extract_text() or ""
        front_text_parts.append(txt)

    # Add tail pages to capture conclusion/appendix signals when available.
    tail_text_parts: list[str] = []
    if total_pages > first_page_count:
        start_tail = max(first_page_count, total_pages - 2)
        for idx in range(start_tail, total_pages):
            txt = reader.pages[idx].extract_text() or ""
            tail_text_parts.append(txt)

    front_text = "\n".join(front_text_parts)
    tail_text = "\n".join(tail_text_parts)

    # Favor introductory pages, then append a small tail section if capacity remains.
    head_budget = int(max_chars * 0.8)
    tail_budget = max_chars - head_budget

    clipped_front = front_text[:head_budget]
    clipped_tail = tail_text[:tail_budget]
    combined = (clipped_front + "\n\n" + clipped_tail).strip()

    if not combined:
        raise PdfSummaryError("Could not extract readable text from the PDF.")

    return combined[:max_chars]


async def summarize_arxiv_pdf(doc_id: str, title: str, body: str) -> tuple[str, bool]:
    """Return full-paper summary for an ArXiv doc, with cache and guardrails."""
    cached = _get_cached_summary(doc_id)
    if cached:
        return cached, True

    _enforce_rate_limit()
    settings = get_settings()

    arxiv_id = _extract_arxiv_id(body)
    pdf_url = build_pdf_url(arxiv_id)

    try:
        async with httpx.AsyncClient(
            timeout=settings.pdf_summary_fetch_timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": "ryu-engine/1.0"},
        ) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except httpx.HTTPStatusError as e:
        raise PdfSummaryError(
            f"Failed to fetch PDF from ArXiv (HTTP {e.response.status_code})."
        ) from e
    except httpx.HTTPError as e:
        raise PdfSummaryError("Failed to download PDF from ArXiv.") from e

    extracted_text = _extract_text_sections(
        pdf_bytes=pdf_bytes,
        max_chars=settings.pdf_summary_max_input_chars,
    )

    try:
        summary = await generate_summary(
            title=title,
            body=extracted_text,
            max_chars=settings.pdf_summary_max_input_chars,
        )
    except Exception as e:
        raise PdfSummaryError(str(e)) from e
    _set_cached_summary(doc_id, summary)
    return summary, False
