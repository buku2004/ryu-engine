"""Chat router — conversational AI with RAG."""

import logging
import uuid
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.chat import ChatRequest, ChatResponse, ChatSource
from app.services.hybrid_search import hybrid_search
from app.services.llm import generate_answer

log = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory session store (swap with Redis/SQLite for production)
_sessions: dict[str, list[dict]] = {}


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message and get an AI-generated answer with source citations."""
    session_id = req.session_id or str(uuid.uuid4())

    # 1. Optionally retrieve context via hybrid search
    sources: list[dict] = []
    chat_sources: list[ChatSource] = []

    if req.search_context:
        try:
            results, _ = await hybrid_search(req.message, limit=5)
            sources = [
                {
                    "id": r.id,
                    "title": r.title,
                    "body": r.body,
                    "author": r.author,
                    "source": r.source,
                }
                for r in results
            ]
            chat_sources = [
                ChatSource(id=r.id, title=r.title, score=r.score)
                for r in results
            ]
        except Exception as e:
            log.warning("Search context retrieval failed: %s", e)

    # 2. Get conversation history
    history = _sessions.get(session_id, [])

    # 3. Generate LLM answer
    try:
        answer = await generate_answer(
            question=req.message,
            sources=sources,
            history=history,
        )
    except Exception as e:
        log.error("LLM generation failed: %s", e)
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            detail = "LLM API quota exceeded. Please check your API key and billing."
        elif "401" in error_msg or "auth" in error_msg.lower():
            detail = "LLM API authentication failed. Please check your API key."
        else:
            detail = "Failed to generate AI response. Please try again later."
        return JSONResponse(status_code=503, content={"detail": detail})

    # 4. Store turn in session history
    _sessions.setdefault(session_id, []).extend(
        [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": answer},
        ]
    )

    return ChatResponse(
        answer=answer,
        sources=chat_sources,
        session_id=session_id,
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Retrieve conversation history for a session."""
    history = _sessions.get(session_id, [])
    return {"session_id": session_id, "messages": history}
