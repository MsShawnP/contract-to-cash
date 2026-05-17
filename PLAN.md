# Contract-to-Cash — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build a portfolio piece that tells the complete money-leak story for a $25M CPG brand — tracing where revenue evaporates between contract and cash receipt. React SPA (Vite, Cloudflare Pages), static JSON data from the Cinderhaven Data Platform. Audience is CEO/CFO. The specific visual approach and narrative structure emerge from data exploration, not prescribed upfront.

## Why this arc, why now

Second buyer-facing consumer of the Cinderhaven Data Platform. Demonstrates revenue operations fluency to C-suite buyers. Platform dependency resolved — substrate is live. Building in parallel with channel-profitability-analysis (may ship first).

## Business question this arc answers

On that deal we signed in Q1 — what did we actually net, and where did the money leak between systems?

## Constraints

- All Cinderhaven numbers must reconcile: $25M revenue, 50 SKUs, 11 retailers, 13,496 deductions, 11,634 shipments
- No Streamlit
- Business story first, claims backed by rigorous analysis
- New synthetic data is acceptable if needed, but must be additive and consistent with existing projects
- Quality over speed, no hard deadline

## Tasks

- [x] Run /clarify to scope the work
- [x] Explore platform data — find the story, identify gaps
- [x] Synthesize DTC payment lifecycle data
- [x] Cross-project reconciliation validation (17 checks pass)
- [x] Define narrative structure and visual approach based on findings
- [x] Build Python export script (summary.json, lifecycle.json, retailers.json)
- [x] Scaffold React SPA (Vite + TypeScript + Recharts + CF Pages)
- [x] Implement anchor waterfall + narrative sections
- [x] Data audit — internal consistency, cross-file reconciliation, realism checks
- [x] DTC backfill — match fct_orders volume (26,333), realistic AOV ($55)
- [x] Headline reframe — loss framing ("Twelve Cents Vanishes")
- [x] Make time-to-cash narrative data-driven
- [ ] Chart polish — axis formatting, data labels, spacing, visual refinements
- [ ] Final deploy to Cloudflare Pages + merge PR

## Out of scope for this arc

- Streamlit or server-rendered apps
- DE proof (platform handles that)
- Marketing/LinkedIn content
- Rebuilding platform infrastructure
- Anything that doesn't serve the story

## Definition of done for this arc

- [ ] Fully deployed React SPA on Cloudflare Pages
- [ ] Complete, compelling money-leak narrative backed by data
- [ ] Numbers reconcile with all other Cinderhaven projects
- [ ] CFO/CEO can understand the story without technical background

---

## Arc history

---

## Improvement history

<!-- Entries are added by /improve — don't delete this section -->
