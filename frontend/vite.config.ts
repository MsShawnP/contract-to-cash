/// <reference types="vitest/config" />
import { readFileSync } from "node:fs";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Fill social/meta preview tokens in index.html from the exported summary.json
 * so the OG/Twitter cards never drift from the shipped data. Tokens:
 *   __CENTS_PER_DOLLAR__  -> summary.combined.cents_per_dollar
 *   __TOTAL_LEAKAGE__     -> summary.combined.total_leakage, formatted $X.XM / $XK
 * Runs in both dev (serve) and build.
 */
function metaFromSummary(): Plugin {
  const formatDollars = (n: number): string => {
    if (n >= 1_000_000) return `$${(n / 1e6).toFixed(1)}M`;
    if (n >= 1_000) return `$${(n / 1e3).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
  };

  return {
    name: "meta-from-summary",
    transformIndexHtml(html: string) {
      const summaryUrl = new URL("./public/json/summary.json", import.meta.url);
      const summary = JSON.parse(readFileSync(summaryUrl, "utf-8"));
      const cents = summary.combined.cents_per_dollar;
      const leakage = formatDollars(summary.combined.total_leakage);
      return html
        .replaceAll("__CENTS_PER_DOLLAR__", String(cents))
        .replaceAll("__TOTAL_LEAKAGE__", leakage);
    },
  };
}

export default defineConfig({
  plugins: [react(), metaFromSummary()],
  build: {
    outDir: "dist",
  },
  test: {
    globals: true,
  },
});
