"""Summarization router — RAG-powered document summarization."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.summarize import (
    PaperSummarizeRequest,
    PaperSummarizeResponse,
)
from app.services.paper_summarizer import (
    PdfSummaryError,
    PdfSummaryRateLimitError,
    summarize_arxiv_pdf,
)
from app.services import typesense_client

log = logging.getLogger(__name__)

router = APIRouter(prefix="/summarize", tags=["summarize"])


@router.post("/paper", response_model=PaperSummarizeResponse)
async def summarize_paper(req: PaperSummarizeRequest):
    """Generate a lightweight full-paper summary on demand for ArXiv docs."""
    try:
        doc = await typesense_client.get_document(req.doc_id)
    except Exception:
        return JSONResponse(status_code=404, content={"detail": "Document not found."})

    if doc.get("source") != "arxiv":
        return JSONResponse(
            status_code=400,
            content={"detail": "Full-paper summary is currently supported for ArXiv docs only."},
        )

    try:
        summary, from_cache = await summarize_arxiv_pdf(
            doc_id=req.doc_id,
            title=doc.get("title", "Untitled"),
            body=doc.get("body", ""),
        )
        return PaperSummarizeResponse(summary=summary, from_cache=from_cache, mode="pdf")
    except PdfSummaryRateLimitError as e:
        return JSONResponse(status_code=429, content={"detail": str(e)})
    except PdfSummaryError as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            detail = "LLM API quota exceeded. Please check your API key and billing."
            status = 429
        elif "401" in error_msg or "auth" in error_msg.lower():
            detail = "LLM API authentication failed. Please check your API key."
            status = 401
        else:
            detail = error_msg or "Full-paper summarization failed."
            status = 422
        return JSONResponse(status_code=status, content={"detail": detail})
    except Exception as e:
        log.error("Full-paper summarization failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"detail": "Full-paper summarization failed. Please try again later."},
        )
