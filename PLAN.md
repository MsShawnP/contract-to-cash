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

- All Cinderhaven numbers must reconcile: $25M revenue, 90 SKUs, 11 retailers, 3,087 deductions, 5,838 shipments
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
- [x] Polish, validate, deploy to Cloudflare Pages

## Out of scope for this arc

- Streamlit or server-rendered apps
- DE proof (platform handles that)
- Marketing/LinkedIn content
- Rebuilding platform infrastructure
- Anything that doesn't serve the story

## Definition of done for this arc

- [x] Fully deployed React SPA on Cloudflare Pages
- [x] Complete, compelling money-leak narrative backed by data
- [x] Numbers reconcile with all other Cinderhaven projects
- [x] CFO/CEO can understand the story without technical background

---

## Arc history

---

## Improvement history

### 2026-05-22 — Improvement pass

- **Trigger:** User-initiated after code review and test addition
- **What was reviewed:** Code quality, tests, dependencies, documentation, git hygiene, security, data reconciliation, workflow files
- **Findings:** 3 critical, 4 important, 3 nice-to-have
- **What was fixed (all 10):**
  1. Closed $1.7M waterfall gap — added Unclassified Shortfall stage
  2. Updated stale README (all numbers matched to current JSON)
  3. Fixed validation script — 29/29 checks pass
  4. Hardened db.py — schema allowlist + require credentials
  5. Aligned DTC chargeback_fee between export and validation
  6. Expanded .gitignore (secrets patterns)
  7. Added security headers (_headers file)
  8. Populated FAILURES.md (3 entries)
  9. Annotated stale HANDOFF numbers with current figures
  10. Added test suites (11 vitest + 7 pytest, all passing)
- **Deferred:** None — all findings addressed
- **Next review:** 2026-06-22
