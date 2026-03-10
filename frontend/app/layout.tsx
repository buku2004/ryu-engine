import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Ryu Engine — AI-Powered Topic Search",
    description:
        "A hybrid search engine combining keyword search, semantic similarity, and AI-powered summarization for research paper discovery.",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <body className="min-h-screen bg-surface text-white antialiased">
                {/* Navigation */}
                <nav className="fixed top-0 left-0 right-0 z-50 glass-card rounded-none border-x-0 border-t-0">
                    <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                        <a href="/" className="flex items-center gap-3 group">
                            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-ryu-400 to-ryu-600 flex items-center justify-center shadow-lg shadow-ryu-500/30 group-hover:shadow-ryu-500/50 transition-shadow">
                                <span className="text-white font-bold text-sm">竜</span>
                            </div>
                            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-ryu-300 bg-clip-text text-transparent">
                                Ryu Engine
                            </span>
                        </a>

                        <div className="flex items-center gap-2">
                            <a
                                href="/"
                                className="px-4 py-2 text-sm text-gray-400 hover:text-white rounded-lg hover:bg-surface-overlay transition-colors"
                            >
                                Search
                            </a>
                            <a
                                href="/analytics"
                                className="px-4 py-2 text-sm text-gray-400 hover:text-white rounded-lg hover:bg-surface-overlay transition-colors"
                            >
                                Analytics
                            </a>
                            <a
                                href="/admin"
                                className="px-4 py-2 text-sm text-gray-400 hover:text-white rounded-lg hover:bg-surface-overlay transition-colors"
                            >
                                Admin
                            </a>
                        </div>
                    </div>
                </nav>

                {/* Main content */}
                <main className="pt-16">{children}</main>
            </body>
        </html>
    );
}
