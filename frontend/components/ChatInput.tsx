"use client";

import { useState, FormEvent } from "react";

interface Props {
    onSend: (message: string) => void;
    loading?: boolean;
}

export default function ChatInput({ onSend, loading }: Props) {
    const [input, setInput] = useState("");

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (input.trim() && !loading) {
            onSend(input.trim());
            setInput("");
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative">
            <div className="glass-card flex items-center gap-3 px-5 py-3 rounded-2xl">
                <input
                    id="chat-input"
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask anything about the indexed topics..."
                    className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none text-sm"
                    disabled={loading}
                />
                <button
                    id="chat-send"
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="p-2.5 bg-gradient-to-r from-ryu-500 to-ryu-600 rounded-xl
                   hover:from-ryu-400 hover:to-ryu-500 disabled:opacity-40
                   transition-all shadow-lg shadow-ryu-500/25"
                >
                    {loading ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <svg
                            className="w-4 h-4 text-white"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                            />
                        </svg>
                    )}
                </button>
            </div>
        </form>
    );
}
