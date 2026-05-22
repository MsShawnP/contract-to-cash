# Contract-to-Cash — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

### 2026-05-22 — Exported JSON data drifted from README and HANDOFF without detection

**Attempted:** Re-exported JSON from Postgres (data platform was updated between sessions). Assumed the README and HANDOFF numbers were still correct.

**Why it didn't work:** The JSON was re-exported against an updated database (different retailer count, different totals), but the README, HANDOFF, and og:meta tags still cited the old numbers. The validation scripts didn't catch it because `validate_exported_json.py` was not run after the re-export, and `validate_cross_project.py` checks full-dataset totals, not the CY2025-scoped subset.

**What we tried instead:** Added the unclassified shortfall stage to close the waterfall, updated README with current numbers, and tightened validation to check that stages sum to the gross-net gap.

**Status:** Resolved

**Tags:** data-drift, validation-gap, stale-documentation

---

### 2026-05-22 — Waterfall chart had $1.7M unaccounted gap

**Attempted:** Exported B2B deduction stages from `fct_retailer_deductions` and used gross/net from `fct_retailer_payments`. Expected stages to account for the full gross-net gap.

**Why it didn't work:** The deductions table only captures categorized deductions ($462K). The payment-level gross-net gap ($2.16M) includes payment shortfalls not linked to specific deduction records. The waterfall chart couldn't visually reconcile from gross to net.

**What we tried instead:** Added an "Unclassified Shortfall" catch-all stage computed as gross - net - sum(categorized stages). This closes the waterfall honestly — the gap is visible and labeled rather than hidden.

**Status:** Resolved

**Tags:** waterfall, data-reconciliation, deduction-gap

---

### 2026-05-16 — Deploy command confusion (Pages vs Workers)

**Attempted:** `wrangler pages deploy dist` to deploy to Cloudflare.

**Why it didn't work:** The project uses Cloudflare Workers (with `wrangler.jsonc` assets config), not Cloudflare Pages. The Pages deploy command returned "Project not found."

**What we tried instead:** Used `wrangler deploy` (Workers), which succeeded.

**Status:** Resolved

**Tags:** deployment, cloudflare, wrangler

