
/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Professional/Enterprise Palette (Linear-style)
                background: "#0f1117", // Very dark blue/gray
                surface: "#1e212b",
                primary: "#5e6ad2",    // Professional Indigo
                primaryHover: "#4e5ac0",
                text: "#ebecf0",
                muted: "#8a8f98",
                border: "#2e323b",
                success: "#22c55e",
                warning: "#eab308",
                error: "#ef4444",
            }
        },
    },
    plugins: [],
}
