"""Pydantic models for documents."""

from pydantic import BaseModel, Field
from typing import Optional


class Document(BaseModel):
    """A single document stored in the search engine."""

    id: str
    title: str
    body: str
    author: str = ""
    created_at: int = 0
    source: str = "unknown"


class DocumentIngest(BaseModel):
    """Payload for manual document ingestion."""

    documents: list[Document]


class RedditIngestRequest(BaseModel):
    """Request body for Reddit ingestion endpoint."""

    subreddit: str = "minecraft"
    limit: int = Field(default=50, ge=1, le=500)
    sort: str = Field(default="hot", pattern="^(hot|new|top)$")


class IngestResponse(BaseModel):
    """Response from an ingestion operation."""

    job_id: str
    documents_queued: int
    status: str = "processing"
