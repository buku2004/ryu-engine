"""Pydantic models for the document summarization endpoint."""

from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    """Request body for the /summarize endpoint."""

    title: str
    body: str


class SummarizeResponse(BaseModel):
    """Response from the /summarize endpoint."""

    summary: str
