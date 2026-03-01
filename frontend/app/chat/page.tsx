"use client";

import { useState, useRef, useEffect } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import SourceBadge from "@/components/SourceBadge";
import { chat as apiChat, ChatSource } from "@/lib/api";

interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: ChatSource[];
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessionId, setSessionId] = useState<string | undefined>();
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async (text: string) => {
        setMessages((prev) => [...prev, { role: "user", content: text }]);
        setLoading(true);

        try {
            const res = await apiChat(text, sessionId);
            setSessionId(res.session_id);
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: res.answer,
                    sources: res.sources,
                },
            ]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "Sorry, something went wrong. Please try again.",
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)]">
            {/* Header */}
            <div className="px-6 py-5 border-b border-white/5">
                <h1 className="text-xl font-bold bg-gradient-to-r from-white to-ryu-300 bg-clip-text text-transparent">
                    Chat with Ryu
                </h1>
                <p className="text-gray-500 text-sm mt-1">
                    Ask questions — Ryu searches the indexed knowledge and generates
                    AI-powered answers with cited sources.
                </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-ryu-400 to-ryu-700 flex items-center justify-center mb-4 shadow-xl shadow-ryu-500/20 animate-pulse-glow">
                            <span className="text-2xl text-white font-bold">竜</span>
                        </div>
                        <p className="text-gray-400 text-lg font-medium mb-2">
                            Start a conversation
                        </p>
                        <p className="text-gray-600 text-sm max-w-md">
                            Ask about any topic in the indexed knowledge base. Ryu will search
                            across all sources and synthesize an answer for you.
                        </p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i}>
                        <ChatMessage role={msg.role} content={msg.content} />
                        {/* Sources */}
                        {msg.sources && msg.sources.length > 0 && (
                            <div className="ml-12 mt-2 flex flex-wrap gap-2">
                                <span className="text-xs text-gray-600">Sources:</span>
                                {msg.sources.map((src) => (
                                    <span
                                        key={src.id}
                                        className="text-xs px-2 py-0.5 rounded-md bg-surface-overlay text-gray-400"
                                        title={src.title}
                                    >
                                        {src.title.slice(0, 40)}
                                        {src.title.length > 40 ? "…" : ""}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start animate-slide-up">
                        <div className="glass-card px-5 py-3 rounded-2xl rounded-bl-md">
                            <div className="flex items-center gap-2">
                                <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-ryu-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                    <div className="w-2 h-2 bg-ryu-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                    <div className="w-2 h-2 bg-ryu-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                </div>
                                <span className="text-xs text-gray-500">Searching & thinking...</span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-6 py-4 border-t border-white/5">
                <ChatInput onSend={handleSend} loading={loading} />
            </div>
        </div>
    );
}
