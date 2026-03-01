import SourceBadge from "./SourceBadge";

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

            {/* Footer */}
            <div className="flex items-center gap-3 flex-wrap">
                <SourceBadge source={source} />
                {match_type && (
                    <span className="text-xs px-2 py-0.5 rounded-md bg-surface-overlay text-gray-400">
                        {match_type}
                    </span>
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
