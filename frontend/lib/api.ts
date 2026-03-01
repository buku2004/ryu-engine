/**
 * Backend API client for the Ryu Engine frontend.
 *
 * All calls go through the Next.js rewrite (/api/* → backend:8000/*),
 * so the browser never hits CORS issues.
 */

const API = "/api";

/* ---------- Types ---------- */

export interface SearchHit {
    id: string;
    title: string;
    body: string;
    author: string;
    source: string;
    score: number;
    match_type: string;
}

export interface SearchResponse {
    query: string;
    mode: string;
    total_found: number;
    results: SearchHit[];
}

export interface ChatSource {
    id: string;
    title: string;
    score: number;
}

export interface ChatResponse {
    answer: string;
    sources: ChatSource[];
    session_id: string;
}

export interface IngestResponse {
    job_id: string;
    documents_queued: number;
    status: string;
}

export interface HealthStatus {
    typesense: string;
    qdrant: string;
    all_healthy: boolean;
}

/* ---------- API Functions ---------- */

export async function search(
    q: string,
    mode: string = "hybrid",
    limit: number = 10,
    offset: number = 0
): Promise<SearchResponse> {
    const params = new URLSearchParams({ q, mode, limit: String(limit), offset: String(offset) });
    const res = await fetch(`${API}/search?${params}`);
    if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
    return res.json();
}

export async function chat(
    message: string,
    sessionId?: string
): Promise<ChatResponse> {
    const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message,
            session_id: sessionId,
            search_context: true,
        }),
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
    return res.json();
}

export async function ingestReddit(
    subreddit: string,
    limit: number = 50,
    sort: string = "hot"
): Promise<IngestResponse> {
    const res = await fetch(`${API}/ingest/reddit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subreddit, limit, sort }),
    });
    if (!res.ok) throw new Error(`Ingest failed: ${res.statusText}`);
    return res.json();
}

export async function getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API}/health/services`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
}
