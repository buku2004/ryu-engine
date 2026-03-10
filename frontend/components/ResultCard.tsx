"use client";

import { useState } from "react";
import SourceBadge from "./SourceBadge";
import { summarize } from "@/lib/api";

interface Props {
    id: string;
    title: string;
    body: string;
    author: string;
    source: string;
    score: number;
    match_type: string;
}

export default function ResultCard({
    title,
    body,
    author,
    source,
    score,
    match_type,
}: Props) {
    const [summary, setSummary] = useState<string | null>(null);
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [summaryError, setSummaryError] = useState("");

    const handleSummarize = async () => {
        if (summary) {
            setSummary(null);
            return;
        }
        setSummaryLoading(true);
        setSummaryError("");
        try {
            const res = await summarize(title, body);
            setSummary(res.summary);
        } catch {
            setSummaryError("Summarization failed. Try again.");
        } finally {
            setSummaryLoading(false);
        }
    };

    return (
        <div className="glass-card p-5 hover:border-ryu-500/20 transition-all animate-slide-up group">
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="text-white font-semibold text-lg leading-snug group-hover:text-ryu-300 transition-colors">
                    {title || "Untitled"}
                </h3>
                <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs text-gray-500 font-mono">
                        {(score * 100).toFixed(0)}%
                    </span>
                </div>
            </div>

            {/* Body preview */}
            <p className="text-gray-400 text-sm leading-relaxed line-clamp-3 mb-4">
                {body || "No content available."}
            </p>

            {/* AI Summary */}
            {summary && (
                <div className="mb-4 p-4 rounded-xl bg-ryu-600/10 border border-ryu-500/20 animate-fade-in">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-ryu-400 to-ryu-600 flex items-center justify-center">
                            <span className="text-[10px] text-white font-bold">竜</span>
                        </div>
                        <span className="text-xs text-ryu-400 font-medium">AI Summary</span>
                    </div>
                    <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                        {summary}
                    </p>
                </div>
            )}

            {summaryError && (
                <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs animate-fade-in">
                    {summaryError}
                </div>
            )}

            {/* Footer */}
            <div className="flex items-center gap-3 flex-wrap">
                <SourceBadge source={source} />
                {match_type && (
                    <span className="text-xs px-2 py-0.5 rounded-md bg-surface-overlay text-gray-400">
                        {match_type}
                    </span>
                )}

                {/* Summarize button */}
                <button
                    onClick={handleSummarize}
                    disabled={summaryLoading}
                    className="text-xs px-3 py-1 rounded-lg bg-ryu-600/10 text-ryu-400 hover:bg-ryu-600/20 transition-colors disabled:opacity-40 flex items-center gap-1.5"
                >
                    {summaryLoading ? (
                        <>
                            <div className="w-3 h-3 border border-ryu-400/30 border-t-ryu-400 rounded-full animate-spin" />
                            Summarizing…
                        </>
                    ) : summary ? (
                        "Hide Summary"
                    ) : (
                        <>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Summarize
                        </>
                    )}
                </button>

                {author && (
                    <span className="text-xs text-gray-500 ml-auto">
                        by {author}
                    </span>
                )}
            </div>
        </div>
    );
}
