import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                ryu: {
                    50: "#eef6ff",
                    100: "#d9eaff",
                    200: "#bcdaff",
                    300: "#8ec3ff",
                    400: "#59a2ff",
                    500: "#337dfc",
                    600: "#1d5df1",
                    700: "#1548de",
                    800: "#183bb4",
                    900: "#19368d",
                    950: "#142256",
                },
                surface: {
                    DEFAULT: "#0f1117",
                    raised: "#161822",
                    overlay: "#1e2030",
                },
                accent: {
                    glow: "#337dfc",
                    warm: "#f59e0b",
                    success: "#10b981",
                    danger: "#ef4444",
                },
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
            animation: {
                "pulse-glow": "pulseGlow 2s ease-in-out infinite",
                "slide-up": "slideUp 0.3s ease-out",
                "fade-in": "fadeIn 0.4s ease-out",
            },
            keyframes: {
                pulseGlow: {
                    "0%, 100%": { boxShadow: "0 0 20px rgba(51,125,252,0.3)" },
                    "50%": { boxShadow: "0 0 40px rgba(51,125,252,0.6)" },
                },
                slideUp: {
                    "0%": { transform: "translateY(10px)", opacity: "0" },
                    "100%": { transform: "translateY(0)", opacity: "1" },
                },
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
            },
        },
    },
    plugins: [],
};

export default config;
