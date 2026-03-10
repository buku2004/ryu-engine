interface Props {
    source: string;
}

const BADGE_STYLES: Record<string, { bg: string; text: string; icon: string }> = {
    reddit: {
        bg: "bg-orange-500/10",
        text: "text-orange-400",
        icon: "📮",
    },
    discord: {
        bg: "bg-indigo-500/10",
        text: "text-indigo-400",
        icon: "💬",
    },
    wiki: {
        bg: "bg-green-500/10",
        text: "text-green-400",
        icon: "📖",
    },
    arxiv: {
        bg: "bg-blue-500/10",
        text: "text-blue-400",
        icon: "📝",
    },
};

const DEFAULT_STYLE = {
    bg: "bg-gray-500/10",
    text: "text-gray-400",
    icon: "📄",
};

export default function SourceBadge({ source }: Props) {
    const style = BADGE_STYLES[source?.toLowerCase()] || DEFAULT_STYLE;

    return (
        <span
            className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg ${style.bg} ${style.text}`}
        >
            <span>{style.icon}</span>
            {source || "Unknown"}
        </span>
    );
}
