"use client";

import { useState, useEffect, useCallback } from "react";
import { getAnalytics, AnalyticsSummary } from "@/lib/api";

export default function AnalyticsPage() {
    const [data, setData] = useState<AnalyticsSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const refresh = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const d = await getAnalytics();
            setData(d);
        } catch {
            setError("Failed to load analytics data.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const maxDayCount =
        data && Object.keys(data.searches_over_time).length > 0
            ? Math.max(...Object.values(data.searches_over_time))
            : 1;

    return (
        <div className="max-w-5xl mx-auto px-6 py-12">
            {/* Header */}
            <div className="flex items-center justify-between mb-10">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-ryu-300 bg-clip-text text-transparent">
                        Search Analytics
                    </h1>
                    <p className="text-gray-500 mt-1">
                        Query trends, latency metrics, and usage insights.
                    </p>
                </div>
                <button
                    onClick={refresh}
                    disabled={loading}
                    className="px-5 py-2 text-sm bg-surface-overlay text-gray-300 rounded-xl hover:text-white transition-colors disabled:opacity-40"
                >
                    {loading ? "Loading…" : "Refresh"}
                </button>
            </div>

            {error && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 mb-8 text-red-400 text-sm">
                    {error}
                </div>
            )}

            {data && (
                <div className="space-y-8 animate-fade-in">
                    {/* Summary cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <StatCard
                            label="Total Searches"
                            value={data.total_searches.toLocaleString()}
                            icon="🔍"
                        />
                        <StatCard
                            label="Unique Queries"
                            value={data.unique_queries.toLocaleString()}
                            icon="✨"
                        />
                        <StatCard
                            label="Avg Latency"
                            value={`${data.avg_latency_ms.toFixed(0)}ms`}
                            icon="⚡"
                        />
                        <StatCard
                            label="Search Modes"
                            value={String(data.mode_breakdown.length)}
                            icon="📊"
                        />
                    </div>

                    {/* Mode breakdown + Top queries row */}
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Mode breakdown */}
                        <div className="glass-card p-6">
                            <h2 className="text-lg font-semibold text-white mb-4">
                                Mode Distribution
                            </h2>
                            {data.mode_breakdown.length === 0 ? (
                                <p className="text-gray-500 text-sm">No data yet.</p>
                            ) : (
                                <div className="space-y-3">
                                    {data.mode_breakdown.map((m) => (
                                        <div key={m.mode}>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-300 capitalize">
                                                    {m.mode}
                                                </span>
                                                <span className="text-gray-500">
                                                    {m.count} ({m.percentage}%)
                                                </span>
                                            </div>
                                            <div className="w-full h-2 bg-surface-overlay rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-ryu-500 to-ryu-400 rounded-full transition-all"
                                                    style={{
                                                        width: `${m.percentage}%`,
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Top queries */}
                        <div className="glass-card p-6">
                            <h2 className="text-lg font-semibold text-white mb-4">
                                Top Queries
                            </h2>
                            {data.top_queries.length === 0 ? (
                                <p className="text-gray-500 text-sm">No data yet.</p>
                            ) : (
                                <div className="space-y-2">
                                    {data.top_queries.map((tq, i) => (
                                        <div
                                            key={tq.query}
                                            className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-surface-overlay transition-colors"
                                        >
                                            <div className="flex items-center gap-3">
                                                <span className="text-xs text-gray-600 font-mono w-5">
                                                    {i + 1}
                                                </span>
                                                <span className="text-sm text-gray-300 truncate max-w-[200px]">
                                                    {tq.query}
                                                </span>
                                            </div>
                                            <span className="text-xs text-gray-500 font-mono">
                                                {tq.count}×
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Searches over time */}
                    {Object.keys(data.searches_over_time).length > 0 && (
                        <div className="glass-card p-6">
                            <h2 className="text-lg font-semibold text-white mb-4">
                                Searches Over Time
                            </h2>
                            <div className="flex items-end gap-1 h-32">
                                {Object.entries(data.searches_over_time).map(
                                    ([day, count]) => (
                                        <div
                                            key={day}
                                            className="flex-1 flex flex-col items-center gap-1"
                                        >
                                            <span className="text-[10px] text-gray-500">
                                                {count}
                                            </span>
                                            <div
                                                className="w-full bg-gradient-to-t from-ryu-600 to-ryu-400 rounded-t-sm min-h-[4px] transition-all"
                                                style={{
                                                    height: `${(count / maxDayCount) * 100}%`,
                                                }}
                                            />
                                            <span className="text-[9px] text-gray-600 truncate w-full text-center">
                                                {day.slice(5)}
                                            </span>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    )}

                    {/* Recent searches table */}
                    <div className="glass-card p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">
                            Recent Searches
                        </h2>
                        {data.recent_searches.length === 0 ? (
                            <p className="text-gray-500 text-sm">
                                No searches recorded yet. Try searching for something!
                            </p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="text-gray-500 text-xs border-b border-white/5">
                                            <th className="text-left py-2 px-3 font-medium">
                                                Query
                                            </th>
                                            <th className="text-left py-2 px-3 font-medium">
                                                Mode
                                            </th>
                                            <th className="text-right py-2 px-3 font-medium">
                                                Results
                                            </th>
                                            <th className="text-right py-2 px-3 font-medium">
                                                Latency
                                            </th>
                                            <th className="text-right py-2 px-3 font-medium">
                                                Time
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.recent_searches.map((r, i) => (
                                            <tr
                                                key={i}
                                                className="border-b border-white/[0.03] hover:bg-surface-overlay transition-colors"
                                            >
                                                <td className="py-2 px-3 text-gray-300 truncate max-w-[200px]">
                                                    {r.query}
                                                </td>
                                                <td className="py-2 px-3">
                                                    <span className="text-xs px-2 py-0.5 rounded-md bg-surface-overlay text-gray-400 capitalize">
                                                        {r.mode}
                                                    </span>
                                                </td>
                                                <td className="py-2 px-3 text-right text-gray-400">
                                                    {r.total_found}
                                                </td>
                                                <td className="py-2 px-3 text-right font-mono text-gray-400">
                                                    {r.latency_ms.toFixed(0)}ms
                                                </td>
                                                <td className="py-2 px-3 text-right text-gray-500 text-xs">
                                                    {new Date(r.timestamp).toLocaleTimeString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Empty state */}
            {!loading && data && data.total_searches === 0 && (
                <div className="text-center py-20">
                    <p className="text-gray-400 text-lg mb-2">No analytics yet</p>
                    <p className="text-gray-600 text-sm">
                        Start searching to see metrics here.
                    </p>
                </div>
            )}
        </div>
    );
}

function StatCard({
    label,
    value,
    icon,
}: {
    label: string;
    value: string;
    icon: string;
}) {
    return (
        <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{icon}</span>
                <span className="text-xs text-gray-500 uppercase tracking-wide">
                    {label}
                </span>
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
        </div>
    );
}
