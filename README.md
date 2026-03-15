# Ryu Engine

AI-powered hybrid search engine for research paper discovery. Combines keyword search (Typesense) with semantic/vector search (Qdrant), merges results using Reciprocal Rank Fusion (RRF), and provides LLM-powered PDF summarization via Gemini.

## Architecture

```
                          +-------------------+
                          |     Browser       |
                          +--------+----------+
                                   |
                                   v
                          +-------------------+
                          |  Next.js Frontend |
                          |   (port 3000)     |
                          |                   |
                          |  /api/* rewrite   |
                          |  proxy to backend |
                          +--------+----------+
                                   |
                                   v
                          +-------------------+
                          |  FastAPI Backend   |
                          |   (port 8000)      |
                          +--+------+-------+-+
                             |      |       |
               +-------------+      |       +--------------+
               |                    |                      |
               v                    v                      v
      +-----------------+  +-----------------+   +-------------------+
      |   Typesense     |  |    Qdrant       |   | Gemini / OpenAI   |
      |  (keyword index)|  | (vector index)  |   | (embeddings +     |
      |   port 8108     |  |  port 6333      |   |  LLM summaries)   |
      +-----------------+  +-----------------+   +-------------------+
                                                          |
                                                          v
                                                 +-------------------+
                                                 |    ArXiv API      |
                                                 |  (paper source)   |
                                                 +-------------------+
```

All frontend API calls go through a Next.js rewrite proxy (`/api/*` → backend). The browser never contacts the backend directly, avoiding CORS and Docker DNS issues.

## How It Works

### Ingestion Pipeline

```
ArXiv API (Atom XML)
    │
    ▼
Parse titles, abstracts, authors, categories, ArXiv IDs
    │
    ▼
Generate embedding vectors (Gemini embedding-001, 768 dims)
    │
    ├──▶ Typesense  — stores full document text for keyword search
    │                  (fields: id, title, body, author, source, pdf_url)
    │
    └──▶ Qdrant     — stores embedding vectors for semantic search
                       (COSINE distance, payload: doc_id, title, body, author, source, pdf_url)
```

1. Papers are fetched from the ArXiv API via HTTP, parsed from Atom XML format
2. Each paper gets a deterministic ID (SHA-256 of the ArXiv ID, first 16 chars)
3. Title + body are cleaned (`clean_text`) and combined into embedding input (`prepare_embedding_text`, truncated to 8000 chars)
4. Embeddings are generated via the Gemini embedding API (or OpenAI, configurable)
5. Documents are upserted into both Typesense (keyword index) and Qdrant (vector index)

### Hybrid Search (Reciprocal Rank Fusion)

```
User query: "transformer attention mechanisms"
    │
    ├──▶ Typesense keyword search ──▶ ranked results [A, B, C, D]
    │
    └──▶ Embed query ──▶ Qdrant vector search ──▶ ranked results [C, E, A, F]
                                                        │
                                                        ▼
                                              Reciprocal Rank Fusion
                                              ─────────────────────
                                              score(doc) = Σ 1/(k + rank + 1)

                                              Example with k=60:
                                              A: keyword rank 0 + vector rank 2
                                                 = 1/61 + 1/63 = 0.0323
                                              C: keyword rank 2 + vector rank 0
                                                 = 1/63 + 1/61 = 0.0323
                                              B: keyword rank 1 only
                                                 = 1/62 = 0.0161
                                                        │
                                                        ▼
                                              Deduplicate, sort by fused score
                                              Tag match_type: "keyword", "semantic",
                                              or "keyword+semantic"
```

The two search backends run **concurrently** via `asyncio.gather`. RRF merging means documents found by both keyword and semantic search get boosted scores, while single-source results still appear. The `k` constant (default 60) controls how much rank position matters.

### PDF Summarization

```
POST /summarize/paper  { "doc_id": "abc123" }
    │
    ├──▶ Check in-memory cache (TTL: 24 hours) ──▶ hit? return cached summary
    │
    ├──▶ Enforce rate limit (20 calls/hour, sliding window)
    │
    ├──▶ Look up document in Typesense, extract ArXiv ID from body
    │
    ├──▶ Download PDF from https://arxiv.org/pdf/{arxiv_id}.pdf
    │
    ├──▶ Extract text via pypdf
    │       • First 6 pages (80% of char budget)
    │       • Last 2 pages  (20% of char budget — captures conclusions)
    │       • Total: max 8000 chars
    │
    └──▶ Send to Gemini LLM (gemini-2.0-flash)
            • Retry up to 3x with exponential backoff on rate-limit errors
            • Cache the result for 24 hours
```

## Project Structure

```
ryu-engine/
├── app/
│   ├── main.py                    # FastAPI app, CORS, lifespan startup
│   ├── config.py                  # Pydantic settings (env vars / .env)
│   ├── routers/
│   │   ├── health.py              # GET /health, GET /health/services
│   │   ├── ingest.py              # POST/GET/DELETE /ingest/*
│   │   ├── search.py              # GET /search, /search/keyword, /search/semantic
│   │   ├── analytics.py           # GET /analytics
│   │   └── summarize.py           # POST /summarize/paper
│   ├── services/
│   │   ├── arxiv_fetcher.py       # ArXiv API client, XML parser
│   │   ├── embedding.py           # Gemini/OpenAI embedding generation
│   │   ├── qdrant_client.py       # Qdrant vector DB operations
│   │   ├── typesense_client.py    # Typesense keyword search operations
│   │   ├── hybrid_search.py       # RRF fusion, search orchestration
│   │   ├── llm.py                 # Gemini/OpenAI LLM calls (RAG + summaries)
│   │   ├── paper_summarizer.py    # PDF download, text extraction, caching
│   │   └── analytics.py           # In-memory search analytics tracker
│   ├── models/
│   │   ├── document.py            # Document, ArxivIngestRequest, IngestResponse
│   │   ├── search.py              # SearchRequest, SearchHit, SearchResponse
│   │   ├── analytics.py           # AnalyticsSummary, TopQuery, ModeBreakdown
│   │   └── summarize.py           # PaperSummarizeRequest/Response
│   └── utils/
│       └── text_processing.py     # clean_text, prepare_embedding_text
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # Root layout, navigation bar
│   │   ├── page.tsx               # Search page (/)
│   │   ├── analytics/page.tsx     # Analytics dashboard (/analytics)
│   │   └── admin/page.tsx         # Admin panel (/admin)
│   ├── components/
│   │   ├── SearchBar.tsx          # Search input with mode toggle
│   │   ├── ResultCard.tsx         # Search result with PDF summarize action
│   │   └── SourceBadge.tsx        # Colored source label badge
│   ├── lib/
│   │   └── api.ts                 # API client (fetch wrappers)
│   ├── next.config.js             # /api/* rewrite proxy to backend
│   ├── tailwind.config.ts         # Dark theme, custom colors, animations
│   └── Dockerfile                 # Multi-stage Node.js build
├── tests/
│   ├── test_arxiv_fetcher.py      # ArXiv parsing, ID generation (18 tests)
│   ├── test_hybrid_search.py      # RRF scoring, PDF URL resolution (7 tests)
│   ├── test_models.py             # Pydantic model validation (8 tests)
│   ├── test_paper_summarizer.py   # Caching, rate limiting, PDF extraction (9 tests)
│   └── test_text_processing.py    # Text cleaning, embedding prep (10 tests)
├── Dockerfile                     # Backend (python:3.13-alpine)
├── docker-compose.yml             # Full stack: backend + frontend + typesense + qdrant
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Ruff + pytest config
└── .env.example                   # Environment variable template
```

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Backend | FastAPI (Python 3.11+) | REST API, async request handling |
| Keyword Search | Typesense 27.1 | Full-text search with faceting |
| Vector Search | Qdrant 1.11 | Nearest-neighbor search (cosine similarity) |
| Embeddings | Gemini `embedding-001` (768 dims) | Convert text to vector representations |
| LLM | Gemini 2.0 Flash / GPT-4 | RAG answers and PDF summarization |
| Frontend | Next.js 14 + Tailwind CSS | Dark-themed UI with glassmorphism design |
| PDF Parsing | pypdf | Extract text from ArXiv PDFs |
| HTTP Client | httpx | Async HTTP for ArXiv API and PDF downloads |
| Testing | pytest + pytest-asyncio | 51 unit tests |
| Linting | Ruff | Python linting and formatting |

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/your-username/ryu-engine.git
cd ryu-engine
cp .env.example .env
```

Edit `.env` and add your Gemini API key (free at [Google AI Studio](https://aistudio.google.com/apikey)).

### 2. Run with Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Typesense | http://localhost:8108 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

### 3. Ingest papers

Via the Admin UI at http://localhost:3000/admin, or via curl:

```bash
curl -X POST http://localhost:8000/ingest/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention", "limit": 50, "category": "cs.AI"}'
```

### 4. Search

```bash
# Hybrid search (keyword + semantic fused via RRF)
curl "http://localhost:8000/search?q=attention+mechanism&mode=hybrid"

# Keyword-only
curl "http://localhost:8000/search?q=attention+mechanism&mode=keyword"

# Semantic-only
curl "http://localhost:8000/search?q=attention+mechanism&mode=semantic"
```

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | App info and docs link |
| `GET` | `/health` | Liveness check |
| `GET` | `/health/services` | Typesense + Qdrant connectivity status |
| `GET` | `/search` | Hybrid search (`?q=...&mode=hybrid\|keyword\|semantic`) |
| `GET` | `/search/keyword` | Keyword-only search via Typesense |
| `GET` | `/search/semantic` | Semantic-only search via Qdrant |
| `POST` | `/ingest/arxiv` | Fetch and index papers from ArXiv |
| `POST` | `/ingest/documents` | Manually ingest documents |
| `GET` | `/ingest/documents` | Browse indexed documents (paginated) |
| `DELETE` | `/ingest/documents/{doc_id}` | Delete a single document |
| `DELETE` | `/ingest/documents` | Purge all documents |
| `POST` | `/summarize/paper` | Generate full-paper PDF summary |
| `GET` | `/analytics` | Search analytics summary |

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| Search | `/` | Main search interface with hybrid/keyword/semantic mode toggle. Results show relevance scores, expandable content, source badges, and a "Summarize PDF" button for ArXiv papers |
| Analytics | `/analytics` | Dashboard with total searches, unique queries, average latency, mode distribution, top queries, searches-over-time chart, and recent search history |
| Admin | `/admin` | Service health checks, ArXiv ingestion form (query, limit, category, sort), document browser with pagination, single/bulk delete |

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google AI API key ([free tier](https://aistudio.google.com/apikey)) |
| `TYPESENSE_API_KEY` | Yes | `xyz` | Typesense API key |
| `LLM_PROVIDER` | No | `gemini` | `gemini` or `openai` |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini chat model |
| `EMBEDDING_MODEL` | No | `gemini-embedding-001` | Embedding model |
| `EMBEDDING_DIMENSIONS` | No | `768` | Vector dimensions |
| `OPENAI_API_KEY` | No | — | Required only if `LLM_PROVIDER=openai` |
| `OPENAI_CHAT_MODEL` | No | `gpt-4` | OpenAI chat model |
| `TYPESENSE_HOST` | No | `localhost` | Typesense host |
| `TYPESENSE_PORT` | No | `8108` | Typesense port |
| `QDRANT_HOST` | No | `localhost` | Qdrant host |
| `QDRANT_PORT` | No | `6333` | Qdrant port |
| `HYBRID_K` | No | `60` | RRF constant (higher = less weight on rank position) |
| `PDF_SUMMARY_MAX_CALLS_PER_HOUR` | No | `20` | PDF summarization rate limit |
| `PDF_SUMMARY_CACHE_TTL_SEC` | No | `86400` | Summary cache lifetime (seconds) |

## Local Development (without Docker)

You still need Typesense and Qdrant running. Start just those with Docker:

```bash
docker compose up typesense qdrant
```

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # configure API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing and Linting

```bash
# Run all tests (51 tests)
pytest tests/ -v

# Lint
ruff check app/ tests/

# Auto-format
ruff format app/ tests/
```

## License

MIT
