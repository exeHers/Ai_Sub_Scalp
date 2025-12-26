import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      backgroundImage: {
        "premium-gradient":
          "radial-gradient(circle at top, rgba(99,102,241,0.25), transparent 60%), radial-gradient(circle at bottom, rgba(236,72,153,0.18), transparent 55%)"
      }
    }
  },
  plugins: []
} satisfies Config;