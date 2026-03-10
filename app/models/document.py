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


class WikiIngestRequest(BaseModel):
    """Request body for wiki ingestion endpoint."""

    wiki: str = Field(default="minecraft", description="Fandom wiki subdomain (e.g. minecraft, zelda)")
    limit: int = Field(default=50, ge=1, le=500)
    category: str = Field(default="", description="Optional category to filter articles (e.g. Blocks, Mobs)")


class IngestResponse(BaseModel):
    """Response from an ingestion operation."""

    job_id: str
    documents_queued: int
    status: str = "processing"
