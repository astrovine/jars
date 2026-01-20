import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core palette - Almost Vantablack
        border: "#1a1a1a",
        input: "#1a1a1a",
        ring: "#10B981",
        background: "#020202",
        foreground: "#EDEDED",

        // Primary - Emerald gradient for money/speed
        primary: {
          DEFAULT: "#10B981",
          foreground: "#020202",
          50: "#ECFDF5",
          100: "#D1FAE5",
          200: "#A7F3D0",
          300: "#6EE7B7",
          400: "#34D399",
          500: "#10B981",
          600: "#059669",
          700: "#047857",
          800: "#065F46",
          900: "#064E3B",
        },

        // Secondary - Subtle dark grays
        secondary: {
          DEFAULT: "#0A0A0A",
          foreground: "#EDEDED",
        },

        // Destructive - Red for losses
        destructive: {
          DEFAULT: "#EF4444",
          foreground: "#ffffff",
        },

        // Muted - Low contrast text
        muted: {
          DEFAULT: "#1a1a1a",
          foreground: "#666666",
        },

        // Accent - Teal for gradients
        accent: {
          DEFAULT: "#14B8A6",
          foreground: "#020202",
        },

        // Card backgrounds
        card: {
          DEFAULT: "#0A0A0A",
          foreground: "#EDEDED",
        },

        // Popover
        popover: {
          DEFAULT: "#0A0A0A",
          foreground: "#EDEDED",
        },

        // Semantic colors
        profit: "#10B981",
        loss: "#EF4444",
        warning: "#F59E0B",
      },

      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "JetBrains Mono", "monospace"],
      },

      fontSize: {
        // Huge display sizes
        "7xl": ["4.5rem", { lineHeight: "1" }],
        "8xl": ["6rem", { lineHeight: "1" }],
        "9xl": ["8rem", { lineHeight: "0.9" }],
        "10xl": ["10rem", { lineHeight: "0.85" }],
      },

      borderRadius: {
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.5rem",
        "3xl": "2rem",
      },

      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
        "30": "7.5rem",
        "128": "32rem",
        "144": "36rem",
      },

      maxWidth: {
        "8xl": "88rem",
        "9xl": "96rem",
      },

      animation: {
        "marquee": "marquee 40s linear infinite",
        "marquee-reverse": "marquee-reverse 40s linear infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-fast": "pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 8s linear infinite",
      },

      keyframes: {
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "marquee-reverse": {
          "0%": { transform: "translateX(-50%)" },
          "100%": { transform: "translateX(0)" },
        },
      },

      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "noise": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
      },

      boxShadow: {
        "glow-sm": "0 0 10px rgba(16, 185, 129, 0.2)",
        "glow": "0 0 20px rgba(16, 185, 129, 0.3), 0 0 40px rgba(16, 185, 129, 0.1)",
        "glow-lg": "0 0 30px rgba(16, 185, 129, 0.4), 0 0 60px rgba(16, 185, 129, 0.2)",
        "inner-glow": "inset 0 0 20px rgba(16, 185, 129, 0.1)",
      },

      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
      },

      transitionDuration: {
        "400": "400ms",
        "600": "600ms",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
