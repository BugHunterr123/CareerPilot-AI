import type { Config } from "tailwindcss";

// Design tokens. One accent colour (deep green), warm neutral greys, two typefaces.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F7F6F2",
        surface: "#FFFFFF",
        line: "#E5E2DA",
        ink: { DEFAULT: "#1C1B19", soft: "#3A3833", muted: "#6B6860", faint: "#9A968C" },
        accent: { DEFAULT: "#1F5C46", hover: "#174836", soft: "#E8F0EB", line: "#B9D2C4" },
        amber: { DEFAULT: "#9A6212", soft: "#FBF2E2", line: "#EBCF9F" },
        danger: { DEFAULT: "#B42318", soft: "#FDEDEB", line: "#F2C1BA" },
        info: { DEFAULT: "#2D5B88", soft: "#EAF1F8", line: "#BCD0E4" },
      },
      fontFamily: {
        sans: ['"Inter Variable"', "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        serif: ['"Source Serif 4 Variable"', "Georgia", "serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      borderRadius: { md: "8px", lg: "10px", xl: "14px" },
      boxShadow: { card: "0 1px 2px rgba(28,27,25,0.04)", pop: "0 8px 24px rgba(28,27,25,0.08)" },
      maxWidth: { content: "1120px" },
    },
  },
  plugins: [],
};
export default config;
