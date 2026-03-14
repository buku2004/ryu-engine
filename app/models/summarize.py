"""Pydantic models for PDF-based document summarization."""

from pydantic import BaseModel


class PaperSummarizeRequest(BaseModel):
    """Request body for on-demand full-paper summarization."""

    doc_id: str


class PaperSummarizeResponse(BaseModel):
    """Response body for full-paper summarization."""

    summary: str
    from_cache: bool = False
    mode: str = "pdf"
