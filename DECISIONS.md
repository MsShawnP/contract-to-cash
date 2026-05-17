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

### 2026-05-16 — Headline: "For Every Dollar Invoiced, Fifty-One Cents Arrives as Cash"
- **Decision:** Use this Economist-style provocative headline.
- **Why:** $15.9M net / $31.4M invoiced = 50.6%. This framing is immediately shocking — it combines AR timing and deductions into a single devastating ratio. It differentiates instantly from RDR (which focuses on deduction recovery, not the full lifecycle). The specificity ("fifty-one cents") is more arresting than a percentage.
- **Scope:** frontend/src/App.tsx (hero section)
- **Do not:** Hedge the headline. The data supports it. Caveats go in supporting text.

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
