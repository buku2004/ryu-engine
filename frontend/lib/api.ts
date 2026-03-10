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

export interface SummarizeResponse {
    summary: string;
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

export interface TopQuery {
    query: string;
    count: number;
}

export interface ModeBreakdown {
    mode: string;
    count: number;
    percentage: number;
}

export interface QueryRecord {
    query: string;
    mode: string;
    total_found: number;
    latency_ms: number;
    timestamp: string;
}

export interface AnalyticsSummary {
    total_searches: number;
    unique_queries: number;
    avg_latency_ms: number;
    top_queries: TopQuery[];
    mode_breakdown: ModeBreakdown[];
    recent_searches: QueryRecord[];
    searches_over_time: Record<string, number>;
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

export async function summarize(
    title: string,
    body: string
): Promise<SummarizeResponse> {
    const res = await fetch(`${API}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, body }),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || `Summarization failed: ${res.statusText}`);
    }
    return res.json();
}

export async function getAnalytics(): Promise<AnalyticsSummary> {
    const res = await fetch(`${API}/analytics`);
    if (!res.ok) throw new Error(`Analytics fetch failed: ${res.statusText}`);
    return res.json();
}

export async function ingestArxiv(
    query: string,
    limit: number = 50,
    category: string = "",
    sortBy: string = "relevance"
): Promise<IngestResponse> {
    const res = await fetch(`${API}/ingest/arxiv`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit, category, sort_by: sortBy }),
    });
    if (!res.ok) throw new Error(`ArXiv ingest failed: ${res.statusText}`);
    return res.json();
}

export async function getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API}/health/services`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
}

export interface BrowseDocument {
    id: string;
    title: string;
    body: string;
    author: string;
    source: string;
}

export interface BrowseResponse {
    documents: BrowseDocument[];
    total: number;
    limit: number;
    offset: number;
}

export async function listDocuments(
    limit: number = 20,
    offset: number = 0
): Promise<BrowseResponse> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    const res = await fetch(`${API}/ingest/documents?${params}`);
    if (!res.ok) throw new Error(`Failed to list documents: ${res.statusText}`);
    return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
    const res = await fetch(`${API}/ingest/documents/${encodeURIComponent(docId)}`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`);
}

export async function purgeAllDocuments(): Promise<{ status: string; typesense_deleted: number }> {
    const res = await fetch(`${API}/ingest/documents`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error(`Purge failed: ${res.statusText}`);
    return res.json();
}
