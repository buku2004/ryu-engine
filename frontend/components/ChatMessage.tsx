interface Props {
    role: "user" | "assistant";
    content: string;
}

export default function ChatMessage({ role, content }: Props) {
    const isUser = role === "user";

    return (
        <div
            className={`flex ${isUser ? "justify-end" : "justify-start"} animate-slide-up`}
        >
            <div
                className={`max-w-[80%] px-5 py-3 rounded-2xl text-sm leading-relaxed ${isUser
                        ? "bg-gradient-to-br from-ryu-500 to-ryu-700 text-white rounded-br-md"
                        : "glass-card text-gray-200 rounded-bl-md"
                    }`}
            >
                {!isUser && (
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-ryu-400 to-ryu-600 flex items-center justify-center">
                            <span className="text-[10px] text-white font-bold">竜</span>
                        </div>
                        <span className="text-xs text-ryu-400 font-medium">Ryu</span>
                    </div>
                )}
                <div className="whitespace-pre-wrap">{content}</div>
            </div>
        </div>
    );
}
