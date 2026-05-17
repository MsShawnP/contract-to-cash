# Contract-to-Cash — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-16 — Use Recharts for waterfall chart
- **Decision:** Use Recharts (not D3) for the anchor waterfall and supporting charts.
- **Why:** The anchor visual is a standard waterfall — no custom path geometry needed. Recharts handles bar/waterfall with less boilerplate than D3, matches short-ship-cost's pattern, and produces SVG for print. D3 would be warranted for a Sankey or force layout, but exploration revealed waterfall is the right chart type.
- **Scope:** frontend/src/components/
- **Do not:** Use D3 unless a chart type emerges that Recharts cannot handle.

---

## Data & Schema

### 2026-05-16 — Revenue frame is fct_payments.gross_amount (not fct_orders.line_total)
- **Decision:** The C2C lifecycle starts at payment-level gross, not invoice totals.
- **Why:** fct_payments.gross_amount ($17.43M) represents what retailers acknowledged they owed. fct_orders.line_total ($31.41M) includes orders not yet paid (AR). The headline uses both — the *invoice-to-cash gap* is the hook, but the *waterfall breakdown* uses the payment frame where we can trace exactly what was deducted.
- **Scope:** All lifecycle calculations, export script, narrative text.
- **Do not:** Present $31.41M as "revenue" without qualifying it as "invoiced."

### 2026-05-16 — DTC payment data lives in raw schema (not dbt-governed)
- **Decision:** DTC payment tables (shopify_transactions, shopify_refunds, shopify_chargebacks, shopify_payouts) written directly to the raw schema in Postgres.
- **Why:** Faster to iterate during C2C development. Adding dbt models/sources would require changes to cinderhaven-data-platform. The export script queries raw directly. If other projects need DTC payments, governance can be added later.
- **Scope:** scripts/generate_dtc_payments.py, scripts/export_json.py
- **Do not:** Modify cinderhaven-data-platform dbt models for C2C-only needs.

---

## Visualization

### 2026-05-16 — Anchor visual is a waterfall chart
- **Decision:** Use a descending waterfall as the anchor visual (gross → deduction categories → net).
- **Why:** Exploration revealed 9 deduction types with clear magnitude ranking. A waterfall shows the starting amount and each category "chipping away" — the viewer literally sees money disappearing step by step. Sankey was considered but is better for flows with multiple destinations (RDR already uses one). Bar charts don't show the cumulative loss.
- **Scope:** frontend/src/components/
- **Do not:** Use a Sankey (that's RDR's visual identity).

### 2026-05-16 — Single-page scrolling narrative structure
- **Decision:** The piece is a single-page scroll with 4 sections: (1) headline + shock stat, (2) anchor waterfall, (3) retailer comparison bars, (4) time-to-cash insight.
- **Why:** The story has a clear arc: shock → breakdown → comparison → timing. A single scroll delivers all three audience reactions (R3) in sequence without navigation. Dashboard-style tabbing would fight the narrative constraint (R10).
- **Scope:** frontend/src/App.tsx
- **Do not:** Add tabs, filters, or multi-page navigation.

### ~~2026-05-16 — Headline: "For Every Dollar Invoiced, Fifty-One Cents Arrives as Cash"~~
- ~~Superseded by 2026-05-17 entry below. Retention framing broke when denominator changed from invoiced to gross payments.~~

### 2026-05-17 — Headline reframed as leakage: "For Every Dollar Collected, Twelve Cents Vanishes in Deductions"
- **Decision:** Use loss framing (leakage cents) instead of retention framing (cents per dollar).
- **Why:** After switching the denominator from invoiced ($16.3M) to gross payments ($21.6M), the retention ratio flipped to 87¢ — not dramatic. Loss framing ("twelve cents vanishes") is mathematically stable regardless of which gross figure is used, and the word "vanishes" is more provocative than "arrives." The headline_ratio field now tracks leakage (0.129), not retention.
- **Scope:** scripts/export_json.py, frontend/src/App.tsx (hero section), summary.json
- **Do not:** Switch back to retention framing — it's fragile to denominator choice.

### 2026-05-17 — DTC volume: backfill transactions to match fct_orders, don't reduce order count
- **Decision:** When DTC payment records (shopify_transactions) are sparse relative to fct_orders, insert additional records rather than reducing the reported order count.
- **Why:** The order count from fct_orders (26,333) represents the real business volume. Reducing it to match sparse payment data understates the business. Backfilling brings AOV to $55 (industry norm) and DTC share to 6.3% of total (in the 5-15% norm range).
- **Scope:** scripts/backfill_dtc.py, raw.shopify_transactions/refunds/chargebacks
- **Do not:** Count DTC orders from shopify_transactions — always use fct_orders.

---

## Deployment

### 2026-05-16 — Deploy to Cloudflare Pages via wrangler
- **Decision:** Ship the SPA as a Cloudflare Workers static site using wrangler deploy from frontend/.
- **Why:** Zero-config static hosting with global CDN. SPA not_found_handling routes all paths to index.html. No server-side logic needed — all data is pre-exported JSON. Workers domain (contract-to-cash.msshawnp.workers.dev) serves as the portfolio URL.
- **Scope:** frontend/wrangler.jsonc, deployment workflow.
- **Do not:** Add a custom domain until the piece is reviewed and finalized.

### 2026-05-16 — Exclude distributors (KeHE, UNFI) from analysis
- **Decision:** Filter all B2B queries by `dim_retailers.channel_type = 'retailer'`, excluding distributors entirely.
- **Why:** Distributors are intermediaries — retailers buy from them. Including distributor payments alongside direct retail payments mixes fundamentally different commercial relationships. The analysis is about what Cinderhaven nets from its retail partners, not from middlemen.
- **Scope:** scripts/export_json.py, all B2B queries, all JSON output.
- **Do not:** Re-add distributors. If distributor analysis is needed, it's a separate piece.

### 2026-05-16 — Scope analysis to Calendar Year 2025
- **Decision:** All queries filter to Jan 1 – Dec 31, 2025.
- **Why:** An 18-month window is unrealistic for a revenue lifecycle review. CFOs look at a fiscal year or quarter. CY2025 is a clean annual frame that produces meaningful numbers ($15.6M invoiced, 59 cents per dollar).
- **Scope:** scripts/export_json.py (PERIOD_START, PERIOD_END constants), all JSON output.
- **Do not:** Use unbounded date ranges. If a different period is needed, change the constants.

### 2026-05-16 — Net Received bar in kelly green (#2D8E47)
- **Decision:** The waterfall chart's Net Received bar uses kelly green, not teal.
- **Why:** The teal gradient shows deductions "chipping away." The final net bar is the result — it needs to visually stand out as a different category (outcome vs. process). Green signals "what you kept."
- **Scope:** frontend/src/components/WaterfallChart.tsx
- **Do not:** Use navy, steel, or teal for the net bar.

---

## Output Formats

---

## Writing & Voice

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
