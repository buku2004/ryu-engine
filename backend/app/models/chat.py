"""Pydantic models for the conversational chat endpoint."""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    message: str
    session_id: Optional[str] = None
    search_context: bool = True


class ChatSource(BaseModel):
    """A source document cited in the AI answer."""

    id: str
    title: str
    score: float = 0.0


class ChatResponse(BaseModel):
    """Response from the /chat endpoint."""

    answer: str
    sources: list[ChatSource] = []
    session_id: str
