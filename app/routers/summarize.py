"""Summarization router — RAG-powered document summarization."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.summarize import SummarizeRequest, SummarizeResponse
from app.services.llm import generate_summary

log = logging.getLogger(__name__)

router = APIRouter(prefix="/summarize", tags=["summarize"])


@router.post("", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    """Generate a concise summary of a document using the LLM."""
    try:
        summary = await generate_summary(title=req.title, body=req.body)
    except Exception as e:
        log.error("Summarization failed: %s", e)
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            detail = "LLM API quota exceeded. Please check your API key and billing."
        elif "401" in error_msg or "auth" in error_msg.lower():
            detail = "LLM API authentication failed. Please check your API key."
        else:
            detail = "Summarization failed. Please try again later."
        return JSONResponse(status_code=503, content={"detail": detail})

    return SummarizeResponse(summary=summary)
