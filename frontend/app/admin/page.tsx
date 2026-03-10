"use client";

import { useState, useCallback } from "react";
import {
    ingestArxiv,
    getHealth,
    listDocuments,
    deleteDocument,
    purgeAllDocuments,
    IngestResponse,
    HealthStatus,
    BrowseDocument,
} from "@/lib/api";

const CATEGORIES = [
    { value: "", label: "All Categories" },
    { value: "cs.AI", label: "Artificial Intelligence" },
    { value: "cs.LG", label: "Machine Learning" },
    { value: "cs.CL", label: "NLP / Computation & Language" },
    { value: "cs.CV", label: "Computer Vision" },
    { value: "cs.SE", label: "Software Engineering" },
    { value: "cs.CR", label: "Cryptography & Security" },
    { value: "cs.DS", label: "Data Structures & Algorithms" },
    { value: "cs.DC", label: "Distributed Computing" },
    { value: "cs.RO", label: "Robotics" },
    { value: "stat.ML", label: "Statistics / ML" },
    { value: "physics", label: "Physics" },
    { value: "math", label: "Mathematics" },
];

const SORT_OPTIONS = [
    { value: "relevance", label: "Relevance" },
    { value: "submittedDate", label: "Newest First" },
    { value: "lastUpdatedDate", label: "Recently Updated" },
];

export default function AdminPage() {
    const [query, setQuery] = useState("machine learning");
    const [limit, setLimit] = useState(50);
    const [category, setCategory] = useState("");
    const [sortBy, setSortBy] = useState("relevance");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<IngestResponse | null>(null);
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [error, setError] = useState("");

    // Document browser state
    const [docs, setDocs] = useState<BrowseDocument[]>([]);
    const [docsTotal, setDocsTotal] = useState(0);
    const [docsOffset, setDocsOffset] = useState(0);
    const [docsLoading, setDocsLoading] = useState(false);
    const [docsLoaded, setDocsLoaded] = useState(false);
    const [purging, setPurging] = useState(false);

    const DOCS_PER_PAGE = 20;

    const handleIngest = async () => {
        setLoading(true);
        setError("");
        setResult(null);
        try {
            const data = await ingestArxiv(query, limit, category, sortBy);
            setResult(data);
            // Refresh document list if it was loaded
            if (docsLoaded) fetchDocs(0);
        } catch (err: any) {
            setError(err.message || "Ingestion failed");
        } finally {
            setLoading(false);
        }
    };

    const handleHealthCheck = async () => {
        try {
            const data = await getHealth();
            setHealth(data);
        } catch {
            setHealth(null);
            setError("Health check failed");
        }
    };

    const fetchDocs = useCallback(async (offset: number) => {
        setDocsLoading(true);
        try {
            const data = await listDocuments(DOCS_PER_PAGE, offset);
            setDocs(data.documents);
            setDocsTotal(data.total);
            setDocsOffset(offset);
            setDocsLoaded(true);
        } catch {
            setError("Failed to load documents");
        } finally {
            setDocsLoading(false);
        }
    }, []);

    const handleDelete = async (docId: string) => {
        try {
            await deleteDocument(docId);
            setDocs((prev) => prev.filter((d) => d.id !== docId));
            setDocsTotal((prev) => prev - 1);
        } catch {
            setError("Failed to delete document");
        }
    };

    const handlePurge = async () => {
        if (!confirm("Delete ALL indexed documents? This cannot be undone.")) return;
        setPurging(true);
        setError("");
        try {
            await purgeAllDocuments();
            setDocs([]);
            setDocsTotal(0);
            setDocsOffset(0);
        } catch {
            setError("Purge failed");
        } finally {
            setPurging(false);
        }
    };

    const totalPages = Math.ceil(docsTotal / DOCS_PER_PAGE);
    const currentPage = Math.floor(docsOffset / DOCS_PER_PAGE) + 1;

    return (
        <div className="max-w-3xl mx-auto px-6 py-12">
            <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-ryu-300 bg-clip-text text-transparent">
                Admin Panel
            </h1>
            <p className="text-gray-500 mb-10">
                Manage data ingestion and monitor service health.
            </p>

            {/* Health check */}
            <div className="glass-card p-6 mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-white">Service Health</h2>
                    <button
                        id="health-check-btn"
                        onClick={handleHealthCheck}
                        className="px-4 py-2 text-sm bg-surface-overlay text-gray-300 rounded-xl hover:text-white transition-colors"
                    >
                        Check Status
                    </button>
                </div>
                {health && (
                    <div className="grid grid-cols-2 gap-4 animate-fade-in">
                        <div className={`p-4 rounded-xl ${health.typesense === "connected" ? "bg-emerald-500/10 border border-emerald-500/20" : "bg-red-500/10 border border-red-500/20"}`}>
                            <p className="text-xs text-gray-500 mb-1">Typesense</p>
                            <p className={`font-medium ${health.typesense === "connected" ? "text-emerald-400" : "text-red-400"}`}>
                                {health.typesense}
                            </p>
                        </div>
                        <div className={`p-4 rounded-xl ${health.qdrant === "connected" ? "bg-emerald-500/10 border border-emerald-500/20" : "bg-red-500/10 border border-red-500/20"}`}>
                            <p className="text-xs text-gray-500 mb-1">Qdrant</p>
                            <p className={`font-medium ${health.qdrant === "connected" ? "text-emerald-400" : "text-red-400"}`}>
                                {health.qdrant}
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* ArXiv ingestion */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-6">
                    ArXiv Paper Ingestion
                </h2>
                <p className="text-gray-500 text-xs mb-5">
                    Search and ingest research papers from ArXiv. Papers are indexed for hybrid search and RAG summarization.
                </p>
                <div className="space-y-5">
                    <div>
                        <label className="block text-sm text-gray-400 mb-2">
                            Search Query
                        </label>
                        <div className="flex items-center glass-card px-4 py-2 rounded-xl">
                            <input
                                id="query-input"
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                className="flex-1 bg-transparent text-white focus:outline-none text-sm"
                                placeholder="e.g. transformer attention, quantum computing"
                            />
                        </div>
                        <p className="text-[10px] text-gray-600 mt-1">
                            e.g. transformer attention, reinforcement learning, LLM alignment
                        </p>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">
                                Limit
                            </label>
                            <input
                                id="limit-input"
                                type="number"
                                value={limit}
                                onChange={(e) => setLimit(Number(e.target.value))}
                                min={1}
                                max={200}
                                className="w-full glass-card px-4 py-2 rounded-xl bg-transparent text-white focus:outline-none text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">
                                Category
                            </label>
                            <select
                                id="category-select"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                className="w-full glass-card px-4 py-2 rounded-xl bg-surface-raised text-white focus:outline-none text-sm border-none"
                            >
                                {CATEGORIES.map((c) => (
                                    <option key={c.value} value={c.value}>
                                        {c.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">
                                Sort By
                            </label>
                            <select
                                id="sort-select"
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                                className="w-full glass-card px-4 py-2 rounded-xl bg-surface-raised text-white focus:outline-none text-sm border-none"
                            >
                                {SORT_OPTIONS.map((s) => (
                                    <option key={s.value} value={s.value}>
                                        {s.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <button
                        id="ingest-btn"
                        onClick={handleIngest}
                        disabled={loading || !query.trim()}
                        className="w-full py-3 bg-gradient-to-r from-ryu-500 to-ryu-600 text-white font-medium rounded-xl
                     hover:from-ryu-400 hover:to-ryu-500 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-all shadow-lg shadow-ryu-500/25"
                    >
                        {loading ? "Ingesting..." : "Start Ingestion"}
                    </button>

                    {/* Result */}
                    {result && (
                        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
                            <p className="text-emerald-400 font-medium text-sm">
                                ✅ Ingestion complete
                            </p>
                            <p className="text-gray-400 text-xs mt-1">
                                {result.documents_queued} documents indexed • Job ID:{" "}
                                <span className="font-mono">{result.job_id.slice(0, 8)}</span>
                            </p>
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 animate-fade-in">
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Document Browser */}
            <div className="glass-card p-6 mt-8">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-lg font-semibold text-white">
                            Indexed Documents
                        </h2>
                        {docsLoaded && (
                            <p className="text-gray-500 text-xs mt-1">
                                {docsTotal} document{docsTotal !== 1 ? "s" : ""} indexed
                            </p>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {docsLoaded && docsTotal > 0 && (
                            <button
                                onClick={handlePurge}
                                disabled={purging}
                                className="px-4 py-2 text-sm bg-red-500/10 text-red-400 rounded-xl hover:bg-red-500/20 transition-colors disabled:opacity-40"
                            >
                                {purging ? "Purging…" : "Purge All"}
                            </button>
                        )}
                        <button
                            onClick={() => fetchDocs(0)}
                            disabled={docsLoading}
                            className="px-4 py-2 text-sm bg-surface-overlay text-gray-300 rounded-xl hover:text-white transition-colors disabled:opacity-40"
                        >
                            {docsLoading ? "Loading…" : docsLoaded ? "Refresh" : "Load Documents"}
                        </button>
                    </div>
                </div>

                {docsLoaded && docs.length === 0 && (
                    <p className="text-gray-500 text-sm text-center py-8">
                        No documents indexed yet. Ingest some ArXiv papers above.
                    </p>
                )}

                {docs.length > 0 && (
                    <div className="space-y-3 animate-fade-in">
                        {docs.map((doc) => (
                            <div
                                key={doc.id}
                                className="flex items-start justify-between gap-4 p-4 rounded-xl bg-surface-overlay/50 hover:bg-surface-overlay transition-colors"
                            >
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-sm font-medium text-white truncate">
                                            {doc.title || "Untitled"}
                                        </h3>
                                        {doc.source && (
                                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400 flex-shrink-0">
                                                {doc.source}
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500 line-clamp-1">
                                        {doc.body || "No content"}
                                    </p>
                                    {doc.author && (
                                        <p className="text-[10px] text-gray-600 mt-1">
                                            by {doc.author}
                                        </p>
                                    )}
                                </div>
                                <button
                                    onClick={() => handleDelete(doc.id)}
                                    className="text-gray-600 hover:text-red-400 transition-colors p-1 flex-shrink-0"
                                    title="Delete document"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                        ))}

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                <button
                                    onClick={() => fetchDocs(docsOffset - DOCS_PER_PAGE)}
                                    disabled={docsOffset === 0 || docsLoading}
                                    className="px-3 py-1.5 text-xs bg-surface-overlay text-gray-400 rounded-lg hover:text-white transition-colors disabled:opacity-30"
                                >
                                    ← Previous
                                </button>
                                <span className="text-xs text-gray-500">
                                    Page {currentPage} of {totalPages}
                                </span>
                                <button
                                    onClick={() => fetchDocs(docsOffset + DOCS_PER_PAGE)}
                                    disabled={currentPage >= totalPages || docsLoading}
                                    className="px-3 py-1.5 text-xs bg-surface-overlay text-gray-400 rounded-lg hover:text-white transition-colors disabled:opacity-30"
                                >
                                    Next →
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
