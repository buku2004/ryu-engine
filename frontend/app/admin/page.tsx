"use client";

import { useState } from "react";
import { ingestReddit, getHealth, IngestResponse, HealthStatus } from "@/lib/api";

export default function AdminPage() {
    const [subreddit, setSubreddit] = useState("minecraft");
    const [limit, setLimit] = useState(50);
    const [sort, setSort] = useState("hot");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<IngestResponse | null>(null);
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [error, setError] = useState("");

    const handleIngest = async () => {
        setLoading(true);
        setError("");
        setResult(null);
        try {
            const data = await ingestReddit(subreddit, limit, sort);
            setResult(data);
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

            {/* Reddit ingestion */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-6">
                    Reddit Ingestion
                </h2>
                <div className="space-y-5">
                    <div>
                        <label className="block text-sm text-gray-400 mb-2">
                            Subreddit
                        </label>
                        <div className="flex items-center glass-card px-4 py-2 rounded-xl">
                            <span className="text-gray-500 text-sm mr-1">r/</span>
                            <input
                                id="subreddit-input"
                                type="text"
                                value={subreddit}
                                onChange={(e) => setSubreddit(e.target.value)}
                                className="flex-1 bg-transparent text-white focus:outline-none text-sm"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
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
                                max={500}
                                className="w-full glass-card px-4 py-2 rounded-xl bg-transparent text-white focus:outline-none text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">
                                Sort
                            </label>
                            <select
                                id="sort-select"
                                value={sort}
                                onChange={(e) => setSort(e.target.value)}
                                className="w-full glass-card px-4 py-2 rounded-xl bg-surface-raised text-white focus:outline-none text-sm border-none"
                            >
                                <option value="hot">Hot</option>
                                <option value="new">New</option>
                                <option value="top">Top</option>
                            </select>
                        </div>
                    </div>

                    <button
                        id="ingest-btn"
                        onClick={handleIngest}
                        disabled={loading || !subreddit.trim()}
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
        </div>
    );
}
