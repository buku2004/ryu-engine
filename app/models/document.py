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


class ArxivIngestRequest(BaseModel):
    """Request body for ArXiv ingestion endpoint."""

    query: str = Field(default="machine learning", description="Search query (e.g. 'transformer attention', 'quantum computing')")
    limit: int = Field(default=50, ge=1, le=200)
    category: str = Field(default="", description="ArXiv category filter (e.g. cs.AI, cs.LG, cs.CV)")
    sort_by: str = Field(default="relevance", description="Sort order: relevance, lastUpdatedDate, submittedDate")


class IngestResponse(BaseModel):
    """Response from an ingestion operation."""

    job_id: str
    documents_queued: int
    status: str = "processing"
