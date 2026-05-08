import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#000",
        s1: "#1c1c1e",
        s2: "#2c2c2e",
        s3: "#3a3a3c",
        bd: "#3a3a3c",
        text: "#f5f5f7",
        t2: "#a1a1a6",
        t3: "#636366",
        blue: "#0a84ff",
        "blue-d": "rgba(10,132,255,0.15)",
        green: "#30d158",
        "green-d": "rgba(48,209,88,0.15)",
        orange: "#ff9f0a",
        "orange-d": "rgba(255,159,10,0.15)",
        red: "#ff453a",
        "red-d": "rgba(255,69,58,0.15)",
      },
      fontFamily: {
        sans: ["DM Sans", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["DM Mono", "ui-monospace", "monospace"],
      },
      animation: {
        blink: "blink 2.5s ease-in-out infinite",
      },
      keyframes: {
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.25" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
