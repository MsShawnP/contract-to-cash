# Contract-to-Cash — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-05-17 — Data audit: DTC backfill, headline reframe, timing made data-driven

**Started from:** Post-realism-audit. Known gaps: DTC volume too low, headline framing broke after denominator change.

**Did:**
- Built comprehensive 59-check audit script (scripts/audit_data.py) — internal consistency, cross-file reconciliation, range checks, structural completeness
- Fixed headline: switched from retention framing ("86 cents arrives") to loss framing ("Twelve Cents Vanishes in Deductions") — stable regardless of denominator choice
- Backfilled raw.shopify_transactions from 6,800 → 26,333 CY2025 records (scripts/backfill_dtc.py), with proportional refunds (1,057) and chargebacks (109 lost)
- DTC gross now $1.45M (6.3% of total, in 5-15% industry norm), AOV $55
- Reverted DTC order count to fct_orders source (26,333) instead of reducing to match sparse payment data
- Made time-to-cash paragraph data-driven (Whole Foods 45.7d, Costco 54.5d, 9-day spread — all derived from retailers.time_to_cash array)
- Added leakage_cents field to combined summary and types
- All 59 audit checks pass, TypeScript compiles clean, browser verified

**Current numbers (CY2025, retailers only):**
- $23.1M combined gross, $20.1M net = 12.9¢ per dollar lost
- B2B: $21.6M gross, $18.7M net, 13.2% leakage, 3,633 deductions
- DTC: $1.45M gross, $1.34M net, 7.3% leakage, 26,333 orders
- 8 retailers, 2,754 B2B orders, 50 SKUs

**State:** 3 commits ahead of origin on `feat/revenue-lifecycle-portfolio`. Not yet pushed or redeployed to Cloudflare.

**Next session:**
- Chart polish: adjust axis formatting, data labels, spacing, and visual refinements across all three charts (waterfall, retailer bars, time-to-cash)
- Push and redeploy to Cloudflare Pages
- Merge PR to main

---

## 2026-05-16 — Realism audit: dataset gaps identified, upstream fix planned

**Started from:** PR open, deployed, all visuals working. User questioned deduction depth and DTC volume.

**Did:**
- Ran comprehensive realism check against mid-market CPG industry norms
- Identified two major gaps: deduction rate (7% vs 10-20% industry) and DTC volume (1.9% vs 5-15% of total)
- Mapped the blast radius: channel-profitability-analysis, short-ship-cost, and cinderhaven-data-platform dbt tests all affected
- Traced generation logic in cinderhaven-data/scripts/11_generate_deductions.py — volume target explicitly set at $750K-$1.2M (3-5%), needs to be $2.5-$3.5M (12-15%)
- DTC issue is AOV ($42 vs $45-80) and order volume — generator produces 10K orders/18mo but at low values
- User decided: fix upstream properly (not export-time scaling), handle as a dedicated new project with CE workflow

**State:** PR still open on `feat/revenue-lifecycle-portfolio`. Current deployment works but has mild numbers. Waiting on upstream data regeneration before final numbers.

**Blocked on:**
- New "dataset improvement" project to handle cinderhaven-data deduction rate tuning + DTC volume increase
- After that ships: re-ingest, re-run dbt, re-export this project, update narrative text, redeploy

**What specifically needs to change here after upstream is fixed:**
- Re-run `scripts/export_json.py` (all JSON will update)
- Headline will change from "Fifty-Nine Cents" to likely "Forty-Five to Fifty Cents"
- Body text with hardcoded retailer names/numbers in App.tsx timing section may need updating
- PR will need additional commits

---

## 2026-05-16 — Polish pass: distributor exclusion, CY2025 scope, color fixes

**Started from:** All 8 units complete, deployed.

**Did:**
- Excluded distributors (KeHE, UNFI) from entire analysis — they're intermediaries, not retail partners
- Scoped all queries to Calendar Year 2025 (was unbounded 18-month window)
- Fixed chart colors to use Lailara teal palette exclusively (removed navy/steel)
- Net Received bar now kelly green (#2D8E47) to distinguish outcome from deduction gradient
- Period label ("Calendar Year 2025") displayed above the fold in brand subtitle
- Fixed retailer spread text bug (min/max instead of array index)
- Redeployed multiple times to Cloudflare Pages
- PR open: https://github.com/MsShawnP/contract-to-cash/pull/1

**State:** Live at https://contract-to-cash.msshawnp.workers.dev. PR has 15 commits on `feat/revenue-lifecycle-portfolio`.

**Current numbers (CY2025, retailers only):**
- $15.6M invoiced, $9.2M net = 59.1 cents per dollar
- 1,593 deductions / $668K total
- 8 retailers, 2,711 B2B orders, 6,800 DTC orders
- 7.0% B2B leakage, 7.1% DTC leakage

**Next:**
- Merge PR to main
- Visual review in browser (screenshot tool times out — charts confirmed via inspect + accessibility)
- Optional: custom domain, Lighthouse audit, og:image asset

---

## 2026-05-16 19:47 — Project initialized

**Started from:** New project setup via /new-project.

**Did:** Created repo, set up CLAUDE.md/DECISIONS.md/HANDOFF.md/PLAN.md/
FAILURES.md, configured project structure.

**State:** Foundation in place. Stack TBD. Ready for /clarify.

**Next:** Run /clarify to scope the work and determine stack.

---
