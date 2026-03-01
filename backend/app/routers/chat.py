"""Chat router — conversational AI with RAG."""

import uuid
from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse, ChatSource
from app.services.hybrid_search import hybrid_search
from app.services.llm import generate_answer

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

    # 2. Get conversation history
    history = _sessions.get(session_id, [])

    # 3. Generate LLM answer
    answer = await generate_answer(
        question=req.message,
        sources=sources,
        history=history,
    )

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
