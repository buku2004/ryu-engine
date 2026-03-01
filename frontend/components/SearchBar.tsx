"use client";

import { useState, FormEvent } from "react";

interface Props {
    onSearch: (query: string, mode: string) => void;
    loading?: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
    const [query, setQuery] = useState("");
    const [mode, setMode] = useState("hybrid");

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (query.trim()) onSearch(query.trim(), mode);
    };

    const modes = [
        { value: "hybrid", label: "Hybrid", icon: "⚡" },
        { value: "keyword", label: "Keyword", icon: "🔤" },
        { value: "semantic", label: "Semantic", icon: "🧠" },
    ];

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
            {/* Search input */}
            <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-ryu-500/20 to-ryu-400/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all opacity-0 group-hover:opacity-100" />
                <div className="relative flex items-center glass-card px-5 py-3 rounded-2xl">
                    <svg
                        className="w-5 h-5 text-gray-500 mr-3 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                    <input
                        id="search-input"
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for anything..."
                        className="flex-1 bg-transparent text-white text-lg placeholder-gray-500 focus:outline-none"
                    />
                    <button
                        id="search-submit"
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="ml-3 px-6 py-2 bg-gradient-to-r from-ryu-500 to-ryu-600 text-white font-medium rounded-xl
                     hover:from-ryu-400 hover:to-ryu-500 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-all shadow-lg shadow-ryu-500/25 hover:shadow-ryu-500/40"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            "Search"
                        )}
                    </button>
                </div>
            </div>

            {/* Mode tabs */}
            <div className="flex justify-center gap-2 mt-4">
                {modes.map((m) => (
                    <button
                        key={m.value}
                        type="button"
                        onClick={() => setMode(m.value)}
                        className={`px-4 py-1.5 text-sm rounded-lg transition-all ${mode === m.value
                                ? "bg-ryu-600/20 text-ryu-300 border border-ryu-500/30"
                                : "text-gray-500 hover:text-gray-300 border border-transparent"
                            }`}
                    >
                        {m.icon} {m.label}
                    </button>
                ))}
            </div>
        </form>
    );
}
