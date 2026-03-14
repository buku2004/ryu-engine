"use client";

import { useState } from "react";
import SourceBadge from "./SourceBadge";
import { summarizePaper } from "@/lib/api";

interface Props {
    id: string;
    title: string;
    body: string;
    author: string;
    source: string;
    pdf_url: string;
    score: number;
    match_type: string;
}

export default function ResultCard({
    id,
    title,
    body,
    author,
    source,
    pdf_url,
    score,
    match_type,
}: Props) {
    const [summary, setSummary] = useState<string | null>(null);
    const [paperSummaryLoading, setPaperSummaryLoading] = useState(false);
    const [summaryError, setSummaryError] = useState("");
    const [summaryMeta, setSummaryMeta] = useState<{
        label: string;
        fromCache?: boolean;
    } | null>(null);
    const [expanded, setExpanded] = useState(false);

    const handlePaperSummarize = async () => {
        if (summary) {
            setSummary(null);
            setSummaryMeta(null);
            return;
        }
        setPaperSummaryLoading(true);
        setSummaryError("");
        try {
            const res = await summarizePaper(id);
            setSummary(res.summary);
            setSummaryMeta({
                label: "Paper Summary",
                fromCache: res.from_cache,
            });
        } catch (err) {
            const message =
                err instanceof Error ? err.message : "Paper summarization failed. Try again.";
            setSummaryError(message);
        } finally {
            setPaperSummaryLoading(false);
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

            {/* Body preview / full content */}
            <p className={`text-gray-400 text-sm leading-relaxed mb-4 whitespace-pre-wrap ${expanded ? "" : "line-clamp-3"}`}>
                {body || "No content available."}
            </p>
            {body && body.length > 200 && (
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-xs text-ryu-400 hover:text-ryu-300 transition-colors mb-4 -mt-2"
                >
                    {expanded ? "Show less ↑" : "Read full content ↓"}
                </button>
            )}

            {/* AI Summary */}
            {summary && (
                <div className="mb-4 p-4 rounded-xl bg-ryu-600/10 border border-ryu-500/20 animate-fade-in">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-ryu-400 to-ryu-600 flex items-center justify-center">
                            <span className="text-[10px] text-white font-bold">竜</span>
                        </div>
                        <span className="text-xs text-ryu-400 font-medium">
                            {summaryMeta?.label || "Paper Summary"}
                        </span>
                        {summaryMeta?.fromCache && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                                cached
                            </span>
                        )}
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

                {source === "arxiv" && (
                    <>
                        <button
                            onClick={handlePaperSummarize}
                            disabled={paperSummaryLoading}
                            className="text-xs px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors disabled:opacity-40"
                        >
                            {paperSummaryLoading
                                ? "Reading PDF..."
                                : summary
                                  ? "Hide Summary"
                                  : "Summarize PDF"}
                        </button>

                        {pdf_url && (
                            <a
                                href={pdf_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-xs px-3 py-1 rounded-lg bg-surface-overlay text-gray-300 hover:text-white transition-colors"
                            >
                                Open PDF
                            </a>
                        )}
                    </>
                )}

                {author && (
                    <span className="text-xs text-gray-500 ml-auto">
                        by {author}
                    </span>
                )}
            </div>
        </div>
    );
}
