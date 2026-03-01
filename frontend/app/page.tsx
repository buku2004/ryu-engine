"use client";

import { useState } from "react";
import SearchBar from "@/components/SearchBar";
import ResultCard from "@/components/ResultCard";
import { search as apiSearch, SearchHit } from "@/lib/api";

export default function Home() {
    const [results, setResults] = useState<SearchHit[]>([]);
    const [total, setTotal] = useState(0);
    const [mode, setMode] = useState("");
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const handleSearch = async (q: string, m: string) => {
        setLoading(true);
        setQuery(q);
        setMode(m);
        setSearched(true);
        try {
            const data = await apiSearch(q, m);
            setResults(data.results);
            setTotal(data.total_found);
        } catch (err) {
            console.error(err);
            setResults([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex flex-col">
            {/* Hero / Search section */}
            <section className="flex flex-col items-center justify-center px-6 pt-24 pb-12">
                {/* Title */}
                <div className="text-center mb-10">
                    <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-4">
                        <span className="bg-gradient-to-r from-white via-ryu-200 to-ryu-400 bg-clip-text text-transparent">
                            Ryu Engine
                        </span>
                    </h1>
                    <p className="text-gray-500 text-lg max-w-xl mx-auto">
                        AI-powered hybrid search — combining keyword precision with
                        semantic understanding.
                    </p>
                </div>

                <SearchBar onSearch={handleSearch} loading={loading} />
            </section>

            {/* Results */}
            {searched && (
                <section className="max-w-4xl mx-auto px-6 pb-16 w-full animate-fade-in">
                    {/* Results header */}
                    <div className="flex items-center justify-between mb-6">
                        <p className="text-sm text-gray-500">
                            {loading
                                ? "Searching..."
                                : `${total} results for "${query}" (${mode})`}
                        </p>
                    </div>

                    {/* Result cards */}
                    <div className="space-y-4">
                        {results.map((hit) => (
                            <ResultCard key={hit.id} {...hit} />
                        ))}
                    </div>

                    {/* Empty state */}
                    {!loading && results.length === 0 && (
                        <div className="text-center py-20">
                            <p className="text-gray-500 text-lg">No results found.</p>
                            <p className="text-gray-600 text-sm mt-2">
                                Try a different query or search mode.
                            </p>
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}
