# Contract-to-Cash — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

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
