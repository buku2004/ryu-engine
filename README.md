# 竜 Ryu Engine

> AI-powered topic-specific hybrid search engine combining keyword precision (Typesense) with semantic understanding (Qdrant + Gemini embeddings) and conversational AI (Gemini 2.0 Flash).

## Architecture

```
Browser  →  Frontend (Next.js :3000)  →  /api/* rewrite proxy
                                              ↓
                                      Backend (FastAPI :8000)
                                         ├─ Typesense (keyword search)
                                         ├─ Qdrant    (vector search)
                                         └─ Gemini    (embeddings + LLM)
```

> **Note:** All frontend API calls use the Next.js rewrite proxy (`/api/*` → backend). The browser never calls the backend directly, avoiding CORS and Docker DNS issues.

## Quick Start

### 1. Clone & configure

```bash
cp .env.example .env
# Add your Gemini API key (free at https://aistudio.google.com/apikey)
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

This starts:
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Typesense | http://localhost:8108 |
| Qdrant | http://localhost:6333 |

### 3. Ingest data

Via the Admin UI at `http://localhost:3000/admin`, or via API:

```bash
curl -X POST http://localhost:8000/ingest/reddit \
  -H "Content-Type: application/json" \
  -d '{"subreddit": "minecraft", "limit": 50}'
```

### 4. Search

```bash
# Hybrid search
curl "http://localhost:8000/search?q=best+redstone+builds&mode=hybrid"

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the best beginner redstone builds?"}'
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Google AI API key ([get free](https://aistudio.google.com/apikey)) |
| `TYPESENSE_API_KEY` | ✅ | Typesense API key (default: `xyz`) |
| `LLM_PROVIDER` | — | `gemini` (default) or `openai` |
| `GEMINI_MODEL` | — | Chat model (default: `gemini-2.0-flash`) |
| `OPENAI_API_KEY` | — | Only needed if `LLM_PROVIDER=openai` |

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # configure API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

> **Note:** You still need Typesense and Qdrant running locally. You can start just those with:
> ```bash
> docker-compose up typesense qdrant
> ```

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Keyword Search:** Typesense
- **Vector Search:** Qdrant
- **Embeddings:** Gemini `gemini-embedding-001` (768 dims)
- **LLM:** Gemini 2.0 Flash (free tier) / GPT-4 (optional)
- **Frontend:** Next.js 14 + Tailwind CSS

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/services` | Typesense + Qdrant status |
| `GET` | `/search` | Hybrid search (`?q=...&mode=hybrid\|keyword\|semantic`) |
| `POST` | `/ingest/reddit` | Fetch & index subreddit posts |
| `POST` | `/ingest/documents` | Manually upload documents |
| `POST` | `/chat` | Conversational AI with RAG |
| `GET` | `/chat/history/{session_id}` | Chat history |

## License

MIT
