# Contract-to-Cash — Full Project Audit

Audit date: 2026-05-17

---

## Phase 1: Baseline Assessment

### What was intended

A portfolio piece telling the complete money-leak story for a $25M CPG
brand. Traces revenue from gross invoiced through net cash received,
showing where and how much evaporates at each stage. Differentiated from
retailer-deduction-recovery (single-stage depth) by lifecycle breadth.
Economist-style provocative headline framing. Audience: CFO/CEO.

**16 requirements** defined in brainstorm doc. Key ones:

- R1: Complete lifecycle story (gross through net cash)
- R2: Economist-style provocative headline
- R3: Three reactions: shock, discovery, comparison
- R5: Numbers reconcile with all Cinderhaven projects
- R8: One anchor visual delivers headline's promise in a single look
- R10: Narrative, not dashboard
- R12: React SPA (Vite), Cloudflare Pages
- R13: Static JSON via Python export script
- R14: Lailara Design System tokens

**8 implementation units** planned (U1-U8), two phases:
discover (explore, synthesize DTC, validate, define story) then
build (export script, scaffold SPA, implement charts, polish + deploy).

---

### What exists today

**Frontend (React SPA) — 10 source files:**

| File | Lines | Role |
|------|-------|------|
| App.tsx | 127 | Single-page scroll with hero, 3 chart sections, footer |
| WaterfallChart.tsx | 167 | Descending waterfall (gross → deduction stages → net) |
| RetailerChart.tsx | 87 | Horizontal bar chart, leakage % by retailer |
| TimeToCashChart.tsx | 94 | Horizontal bar chart, avg days to cash by retailer |
| data.ts | 21 | JSON loader (parallel fetch of 3 files) |
| types.ts | 80 | TypeScript interfaces for all data shapes |
| styles.css | 287 | Full CSS with design tokens, mobile, print |
| main.tsx | ~10 | React entry point |
| index.html | 20 | HTML shell with og:meta tags |
| vite-env.d.ts | ~3 | Vite type reference |

**Static JSON data — 3 files:**

| File | Content |
|------|---------|
| summary.json | Headline numbers: $15.6M invoiced, $9.2M net, 59.1c/dollar |
| lifecycle.json | Waterfall stages: 9 B2B deduction types + 3 DTC categories |
| retailers.json | Per-retailer leakage, time-to-cash, deduction mix (8 retailers) |

**Python scripts — 4 files:**

| Script | Lines | Role |
|--------|-------|------|
| explore_lifecycle.py | 315 | Exploration queries (Phase 1) |
| generate_dtc_payments.py | 390 | DTC payment synthesis to raw schema |
| export_json.py | 416 | Production JSON export (scoped CY2025, retailers only) |
| validate_cross_project.py | 225 | 17 reconciliation checks (exit 0/1) |

**Config:**

- Vite + TypeScript (React 19, Recharts 2.15)
- Cloudflare Workers deployment (wrangler.jsonc, SPA routing)
- Self-hosted fonts (4 woff2 files)

**Documentation:**

- Brainstorm doc with 16 requirements, acceptance examples, success criteria
- Plan doc with 8 implementation units, technical design, risks
- DECISIONS.md with 8 logged decisions
- FAILURES.md — empty
- HANDOFF.md — 2 entries (init + polish session)
- README.md — 3 lines

**Deployment:**
Live at cash.lailarallc.com. PR #1 merged to main.

---

### Current numbers (CY2025, retailers only)

| Metric | Value |
|--------|-------|
| Total invoiced (B2B + DTC) | $15.6M |
| Net cash received | $9.2M |
| Cents per dollar invoiced | 59.1c |
| B2B leakage rate | 7.0% |
| DTC leakage rate | 7.1% |
| B2B retailers | 8 (distributors excluded) |
| Deductions | 1,593 at $668K |
| B2B orders | 2,711 |
| DTC orders | 6,800 |

---

### Gaps between intent and reality

**1. PLAN.md is stale.**
Tasks 5-8 (export script, scaffold SPA, implement charts, deploy) are
unchecked, but all are complete and deployed. HANDOFF.md accurately
reflects this — the plan file was not updated.

**2. og:meta tags contain stale numbers.**
`index.html` line 8-9 reference "fifty-one cents" and "$31.8M" — from
the pre-CY2025-scope era. Current headline is "fifty-nine cents" and
invoiced total is $15.6M. These will show in link previews (LinkedIn,
Slack, etc.) with wrong numbers.

**3. Headline changes with data scope.**
The original headline decision ("fifty-one cents") was based on
unbounded 18-month data. After scoping to CY2025, the number shifted
to 59 cents. DECISIONS.md still records the original headline text.

**4. No frontend tests.**
`tests/CLAUDE.md` defines conventions but `tests/` contains no actual
test files. The SPA has zero automated tests (no unit tests, no
integration tests, no Lighthouse checks).

**5. No CI/CD.**
No GitHub Actions, no automated build, no automated deployment pipeline.
Deploys are manual `wrangler deploy`.

**6. FAILURES.md is empty.**
Git history shows substantial iteration (distributor exclusion, CY2025
scope, color fixes, multiple redeploys) but none were logged as failures.

**7. README is minimal.**
Three lines. No build instructions, no architecture overview, no
screenshots, no deployment instructions. Anyone landing on the repo
gets nothing useful.

**8. Post-merge commits exist on other branches.**
Commits after the merge (e41a9b6 through cedde5a) appear on branches
not yet merged to main — dataset realism fixes, tsbuildinfo gitignore,
timing investigation scripts. Main may be behind.

**9. No accessibility audit.**
No ARIA labels on charts, no skip-navigation link, no tested screen
reader experience. Recharts SVG charts may be opaque to assistive
technology.

**10. No Lighthouse / performance baseline.**
No recorded performance metrics. Font loading strategy (font-display:
swap) is present but no verification of FOUT/FOIT behavior.

**11. Unused data: deduction_mix in retailers.json.**
The `deduction_mix` object (per-retailer deduction type breakdown) is
exported and shipped in the JSON bundle but never rendered in the UI.
It's ~350 lines of JSON payload served to every visitor for no purpose.

---

### Requirement coverage

| Req | Status | Notes |
|-----|--------|-------|
| R1 Complete lifecycle | Done | Gross → deductions → net shown |
| R2 Economist headline | Done | "For Every Dollar Invoiced, Fifty-Nine Cents Arrives as Cash" |
| R3 Three reactions | Done | Shock (hero) → discovery (waterfall) → comparison (retailers) |
| R4 Economist voice | Done | Prose is sober and declarative |
| R5 Numbers reconcile | Partial | CY2025 scope changes canonical surface — validation script checks full dataset, not CY2025 subset |
| R6 DTC data additive | Done | raw schema tables, B2B unaffected |
| R7 Claims traceable | Done | export_json.py has clear SQL per figure |
| R8 Anchor visual | Done | Waterfall chart delivers the promise |
| R9 Economist chart style | Done | Minimal, text-labeled, no decoration |
| R10 Narrative not dashboard | Done | Single-page scroll, no interactivity |
| R11 Supporting detail subordinate | Done | Retailer + timing sections below anchor |
| R12 React SPA / Vite / CF Pages | Done | Deployed and live |
| R13 Static JSON | Done | 3 files, pre-aggregated |
| R14 Lailara Design System | Mostly | Tokens applied; teal palette used; a few small deviations |
| R15 Discovery-driven | Done | 4-phase discovery happened |
| R16 Exploration answers questions | Done | explore_lifecycle.py answered all |

---

### Summary: what's the gap?

The project is **functionally complete and deployed**. The core story
works — a CFO visiting the site sees the lifecycle, the waterfall, the
retailer comparison, and the timing insight. The build followed the plan
faithfully through 8 implementation units.

The gaps are in **polish, hygiene, and portfolio-readiness**:
stale metadata, no tests, no CI, an empty failure log, a minimal README,
unused data in the bundle, and accessibility unknowns. These are the
kinds of things that separate "it works" from "it's ready for
professional scrutiny."

---

## Phase 2: Internal Review

Reviewed across 8 dimensions. Findings ranked by leverage — the
combination of impact (how much damage or missed value) and ease of
fix (how quickly it can be addressed).

---

### Dimension 1: Data Integrity

The most important dimension for a portfolio piece that claims
"every number is traceable."

**F1. Hardcoded prose will break on re-export.** [HIGH]
`App.tsx:64` says "Nine categories of deductions." `App.tsx:85` says
"eight direct retail partners." `App.tsx:99-104` hardcodes specific
retailer names ("Whole Foods", "Costco"), specific day counts (46, 56),
and the computed spread ("ten-day"). None of these come from data.
If `export_json.py` is re-run with different parameters (different
period, different filters), every hardcoded number in the prose
becomes silently wrong. The waterfall and bar charts would update
correctly — but the English text around them would contradict them.

**Fix:** Make prose data-driven. Compute fastest/slowest from
`retailers.time_to_cash`, derive stage count from
`lifecycle.b2b.stages.length`, derive retailer count from
`retailers.leakage.length`.

**F2. og:meta tags contain stale numbers.** [HIGH]
`index.html:8-9` says "fifty-one cents" and "$31.8M". The live data
says 59 cents and $15.6M. Anyone sharing this link on LinkedIn, Slack,
or Twitter sees wrong numbers in the card preview. For a portfolio
piece where credibility is the product, this is a first-impression bug.

**Fix:** Update meta tags to match current data. Consider generating
index.html from a template during build to prevent drift.

**F3. Hardcoded SKU count in export script.** [MEDIUM]
`export_json.py:192` has `"skus": 90` — a literal, not queried from
`dim_products`. If the platform dataset changes, this number is wrong
and nothing catches it.

**Fix:** Query `SELECT COUNT(*) FROM dim_products`.

**F4. Validation gap for CY2025 subset.** [MEDIUM]
`validate_cross_project.py` checks the full 18-month dataset (3,087
deductions, $31.4M orders). But the SPA shows CY2025-scoped data
(1,593 deductions, $15.6M). There is no automated check that the
CY2025 subset is internally consistent — that gross minus deductions
equals net, that per-retailer leakage sums to the total, etc.
A filter bug in export_json.py would produce silently wrong
CY2025 numbers that pass validation.

**Fix:** Add a section to validate_cross_project.py (or a separate
script) that validates the exported JSON files directly.

---

### Dimension 2: Code Quality

**F5. TEAL_SCALE duplicated across 3 components.** [LOW]
The same 8-element array appears identically in `WaterfallChart.tsx:25`,
`RetailerChart.tsx:17`, and `TimeToCashChart.tsx:17`. If the palette
changes (the Lailara design system evolves), three files need updating.
Not urgent for 3 files, but the project CLAUDE.md explicitly says to
use the Lailara Design System tokens.

**Fix:** Extract to a shared `palette.ts` or `theme.ts` module.

**F6. Two different dollar formatting functions.** [LOW]
`App.tsx:8` has `formatM()` (millions only). `WaterfallChart.tsx:38`
has `formatDollars()` (millions + thousands). They behave differently
for the same input range. If a number crosses a threshold, formatting
is inconsistent across the page.

**Fix:** Use one shared formatter.

**F7. Hardcoded color values in chart SVG.** [LOW]
Chart components use inline hex values (`"#e5e0d8"`, `"#6b6b6b"`,
`"#2a2a2a"`) that duplicate CSS custom properties. This is partly
unavoidable with Recharts (SVG fill can't reference CSS variables
without workarounds), but it creates two sources of truth for the
design system.

**Fix:** Define chart colors in a shared constants file that both
CSS and components reference. Or accept the duplication and document
it as a known limitation.

**F8. TypeScript config is solid.** [POSITIVE]
`strict: true`, `noUnusedLocals`, `noUnusedParameters`,
`noFallthroughCasesInSwitch`, `noUncheckedSideEffectImports` — all
the right strictness flags are on. React StrictMode is enabled.
This is better than most portfolio projects.

---

### Dimension 3: Architecture

**F9. Architecture is clean and appropriate.** [POSITIVE]
Clean separation: `types.ts` → `data.ts` → components → `App.tsx`.
No unnecessary abstractions. No state management library (correct —
data is static). No routing (correct — single page). Parallel JSON
loading with `Promise.all`. Each chart component is self-contained.
The Python scripts follow a consistent pattern. Architecture choices
match the project's scope.

**F10. No error boundary.** [MEDIUM]
If any chart component throws a runtime error (e.g., malformed data,
Recharts edge case), the entire page crashes to the React error
screen. A single error boundary around each chart section would
contain the blast radius and show the rest of the page.

**Fix:** Add an `ErrorBoundary` component wrapping each chart section.

---

### Dimension 4: Performance

**F11. Unused deduction_mix data shipped to every visitor.** [LOW]
`retailers.json` contains a `deduction_mix` object (~8KB of JSON)
that is loaded into memory but never rendered. The `Retailers`
TypeScript type includes it, `data.ts` fetches it, but no component
reads it. Dead payload on every page load.

**Fix:** Either remove it from the export and the type, or build
the UI that uses it.

**F12. No JSON preload hints.** [LOW]
HTML loads → JavaScript loads → JSON fetches start. Adding
`<link rel="preload" as="fetch" href="/json/summary.json">` (etc.)
would start JSON downloads in parallel with JavaScript parsing.
Probably saves 50-100ms on slow connections.

**F13. Recharts bundle size.** [INFO]
Recharts typically adds ~200KB gzipped to the bundle. For 3 simple
bar charts, this is heavy. Not worth changing — the project is
deployed and working — but worth noting for future reference. A
lighter alternative (e.g., direct SVG or a micro-charting library)
would cut bundle size significantly.

---

### Dimension 5: Security

**F14. Attack surface is minimal.** [POSITIVE]
No user input. No forms. No auth. No database queries from the
frontend. No API calls beyond static JSON fetches from the same
origin. The security posture is strong by virtue of simplicity.

**F15. No Content-Security-Policy headers.** [LOW]
Cloudflare Workers can serve CSP headers via wrangler config or a
`_headers` file. For a static site with no inline scripts and no
external resources, a strict CSP is trivial and adds defense-in-depth.

---

### Dimension 6: UX / Accessibility

**F16. Charts are opaque to assistive technology.** [MEDIUM]
Recharts SVG output has no `aria-label`, no `role="img"`, no
screen-reader-accessible text alternative. A visually impaired user
encountering the waterfall chart gets meaningless SVG path data.
For a portfolio piece claiming to respect the reader's intelligence,
this is an inconsistency.

**Fix:** Add `role="img"` and `aria-label` to chart containers with
a text summary of the data (e.g., "Waterfall chart showing gross
payments of $9.6M declining through 9 deduction categories to net
received of $8.9M").

**F17. No skip-navigation link.** [LOW]
Single-page scroll with 4 sections. A skip-nav link (hidden until
focused) would let keyboard users jump to content.

**F18. Print styles exist but are untested.** [LOW]
`styles.css:248-287` has `@page` and `@media print` rules including
page size, margin, break-inside avoidance, and a running footer.
These were never verified in a print preview. Recharts SVG should
print well, but chart container heights may cause unexpected page
breaks.

---

### Dimension 7: DevEx / Tooling

**F19. No Python dependency manifest.** [MEDIUM]
The 4 Python scripts require `psycopg2` (or `psycopg2-binary`) but
there is no `requirements.txt`, `pyproject.toml`, or `setup.cfg`.
Anyone cloning the repo has to read the imports to figure this out.

**Fix:** Add `requirements.txt` with `psycopg2-binary`.

**F20. No linting or formatting config.** [LOW]
No ESLint, no Prettier, no Biome. TypeScript strict mode catches
type errors but not style drift. For a solo project this is fine;
for a portfolio piece that might be inspected, consistent formatting
is free credibility.

**F21. No CI/CD pipeline.** [MEDIUM]
No GitHub Actions workflow. Build, typecheck, and deploy are all
manual. A minimal workflow (typecheck on push, deploy on merge to
main) would prevent shipping broken TypeScript.

---

### Dimension 8: Documentation

**F22. README.md is 3 lines.** [HIGH]
For a portfolio piece, the GitHub repo *is* part of the portfolio.
A technical reviewer clicking through from the live site sees: a
3-line description, no screenshot, no build instructions, no
architecture overview, no live URL. This is a missed opportunity
to demonstrate engineering communication skills.

**Fix:** README should have: one-paragraph description, screenshot
of the live piece, live URL, "how to build" instructions, data
pipeline overview, tech stack, and a link to the brainstorm/plan
docs.

**F23. PLAN.md tasks 5-8 unchecked.** [LOW]
The plan says these are incomplete. Reality says they're done and
deployed. A reviewer cross-referencing PLAN.md with the live site
would be confused.

**Fix:** Check off the completed tasks.

---

### Top 10 opportunities ranked by leverage

| Rank | Finding | Impact | Effort | Dimension |
|------|---------|--------|--------|-----------|
| 1 | F2: Stale og:meta tags | High — wrong link previews | 5 min | Data |
| 2 | F1: Hardcoded prose breaks on re-export | High — silent incorrectness | 30 min | Data |
| 3 | F22: README is 3 lines | High — first impression for repo visitors | 30 min | Docs |
| 4 | F16: Charts inaccessible to screen readers | Medium — accessibility gap | 15 min | A11y |
| 5 | F4: No validation for CY2025 subset | Medium — undetectable errors | 30 min | Data |
| 6 | F10: No error boundary | Medium — full page crash risk | 15 min | Arch |
| 7 | F19: No Python requirements.txt | Medium — setup friction | 5 min | DevEx |
| 8 | F21: No CI/CD | Medium — manual deploy risk | 20 min | DevEx |
| 9 | F3: Hardcoded SKU count | Medium — silent drift | 5 min | Data |
| 10 | F23: PLAN.md tasks unchecked | Low — confusing to readers | 2 min | Docs |

---

### What's working well

Things that should be preserved, not refactored:

- **Architecture:** Clean, minimal, appropriate for scope. No over-engineering.
- **TypeScript strictness:** All the right flags enabled.
- **Design system adherence:** Lailara tokens used consistently (fonts, colors, layout).
- **Data pipeline:** Clear SQL, traceable queries, reconciliation validation.
- **Narrative structure:** The story works — shock, breakdown, comparison, timing.
- **Deployment:** Cloudflare Workers with SPA routing, zero-config.
- **Print CSS:** Exists and is thoughtful (page breaks, running footer).
- **Responsive design:** Mobile breakpoint with appropriate type scale changes.

---

## Phase 3: Landscape Scan

### Search methodology

Searched for comparable projects across 5 categories: revenue waterfall
visualizations, CPG analytics portfolios, Economist-style data narratives,
financial data storytelling, and React data viz portfolios. Also scanned
the CPG vendor landscape (trade promotion, deduction management) and
data journalism techniques.

**Key finding: no exact comparable exists.** There is no other public
portfolio piece that tells a CPG revenue lifecycle story as a narrative
SPA. This is genuinely unique positioning.

---

### Comparable projects

**1. celiaongsl/recharts-waterfall** (GitHub)
React + Recharts waterfall chart tutorial. Demonstrates the same
stacked-bar technique C2C uses (base + value bars). Pure tech demo —
no business narrative, no audience framing, no prose.
*Relevance:* Tech reference only. C2C is leagues beyond this in
purpose and polish.

**2. thesjanse/Revenue-Waterfall** (GitHub)
Salesforce data wrangling into an Excel ASC 606 revenue waterfall.
Closest prior art for the *data pipeline* side — extracting revenue
stages from a CRM and mapping them to a waterfall — but the output
is Excel, not a web narrative.
*Relevance:* Shows the pipeline pattern exists in the wild. C2C
modernizes it into a shareable, web-native format.

**3. SankeyArt** (sankeyart.com)
Web tool generating Sankey diagrams from income statements (Apple,
Alphabet, Microsoft, Tesla). Explicitly argues Sankey is superior to
waterfall for income-statement stories because it shows *structural
relationships*, not just sequential subtraction. Their critique:
waterfall "is not very intuitive to most people."
*Relevance:* The Sankey-vs-waterfall argument is addressed in
DECISIONS.md — Sankey is RDR's visual identity, waterfall is C2C's.
The differentiation is deliberate. But the critique is worth noting.

**4. NYT Buy vs. Rent Calculator** (nytimes.com/interactive)
Financial narrative for a non-data-scientist audience (homebuyers).
User inputs drive a single decisive output. Interactive but
narrative-first. The mechanism — personalizable inputs that change
the story — is something C2C currently lacks.
*Relevance:* Pattern for a future "bring your own numbers" mode.

**5. FT / John Burn-Murdoch annotation discipline**
FT's chart philosophy: titles make claims (not describe charts),
annotations guide the eye through a Z-pattern, every annotation
earns its place. "If you have a title that makes a point, you're
going to get a stronger reaction."
*Relevance:* C2C's section titles are descriptive ("Where the Money
Goes") rather than claim-making ("Seven Cents of Every Dollar
Vanishes"). The headline is strong; the section titles are not.

**6. ProPublica / Guardian scrollytelling** (longform data journalism)
Scroll triggers advance a narrative in discrete beats — each scroll
step reveals one finding. The CPG waterfall story has the same
structure: each deduction step is a beat that could be revealed
progressively.
*Relevance:* Pattern for a future scrollytelling upgrade. Current
"show everything at load" is fine for a portfolio piece but
scroll-triggered reveal would make the 41% revenue leak feel like
a discovery.

**7. CPG vendor tools** (Enable, Flintfox, Oracle CPQ, UpClear, TrewUp)
SaaS platforms offering "price waterfall" views inside CPG pricing
systems — list price through deduction tiers to pocket price. All
are logged-in dashboards. None produce shareable narratives.
*Relevance:* Confirms that CFOs *expect* waterfall vocabulary.
C2C speaks the right language. The format differentiator (shareable
URL vs. logged-in BI tool) is real and valuable.

**8. Observable HQ** (observablehq.com)
Reactive JavaScript notebooks with D3. Used by data journalists
for exploration. Has d3-sankey collection. No CPG-specific revenue
lifecycle notebooks exist publicly.
*Relevance:* C2C is the polished, CFO-ready version of what would
otherwise live in a notebook. The gap between "exploratory notebook"
and "shareable narrative SPA" is exactly what C2C fills.

---

### Feature matrix

| Feature | C2C | Vendor dashboards | Observable notebooks | Data journalism | GitHub demos |
|---------|-----|-------------------|---------------------|-----------------|-------------|
| Narrative-driven (not dashboard) | **Yes** | No | No | **Yes** | No |
| Shareable URL (no login) | **Yes** | No | Partial | **Yes** | **Yes** |
| CPG domain vocabulary | **Yes** | **Yes** | No | No | No |
| CFO/CEO audience framing | **Yes** | Partial | No | Partial | No |
| Waterfall visual | **Yes** | **Yes** | Partial | Rare | **Yes** |
| Economist chart style | **Yes** | No | No | **Yes** | No |
| Data pipeline (SQL → JSON) | **Yes** | N/A | Inline | N/A | No |
| Cross-project validation | **Yes** | N/A | No | No | No |
| Self-hosted fonts | **Yes** | N/A | No | **Yes** | No |
| Print CSS | **Yes** | No | No | Partial | No |
| Mobile responsive | **Yes** | **Yes** | Partial | **Yes** | Partial |
| Interactive (user inputs) | No | **Yes** | **Yes** | Some | No |
| Scroll-triggered narrative | No | No | No | **Yes** | No |
| Claim-making section titles | No | N/A | N/A | **Yes** | No |
| Accessibility (a11y) | No | Varies | No | **Yes** (major pubs) | No |
| Real data / live connection | No (static JSON) | **Yes** | **Yes** | **Yes** | No |

---

### Where C2C sits

**Unique strengths (no comparable does all of these):**
- Narrative + CPG domain + shareable URL + Economist style
- Data pipeline with cross-project reconciliation
- The combination of a polished SPA with a real data engineering
  backend is not found in any public portfolio project

**Better than comparables:**
- More polished than any GitHub waterfall demo
- More narrative than any vendor dashboard
- More domain-specific than any data journalism piece
- More production-grade than any Observable notebook

**Gaps relative to the best in each category:**

| Gap | Who does it better | Severity for C2C |
|-----|--------------------|------------------|
| No interactivity (can't swap numbers) | NYT calculators, vendor tools | Low — narrative piece, not a tool |
| No scroll-triggered reveal | ProPublica, Guardian | Medium — would strengthen the "discovery" beat |
| Section titles describe, don't claim | FT annotation discipline | Medium — low effort, high impact on narrative punch |
| No accessibility | Major data journalism outlets | Medium — addressed in Phase 2 (F16) |
| No "bring your own data" mode | Vendor tools | Low — out of scope for this arc |

---

### Industry benchmark validation

CPG industry norms (from vendor literature and trade sources):
- Trade spend = 15–25% of gross sales
- Invalid deductions = 5–10% of trade claims
- Days-to-cash for retail = 30–90 days typical

C2C's synthetic data:
- B2B leakage = 7.0% (within 5–10% range)
- DTC leakage = 7.1% (within realistic range for Shopify fees + refunds)
- Days-to-cash = 46–56 days (within 30–90 range)

The numbers pass the CFO sniff test. A domain expert would not flag
these as unrealistic.

---

### Key landscape takeaway

C2C occupies a genuinely empty niche: **a narrative-first, domain-specific,
shareable revenue lifecycle analysis with a production data pipeline
behind it.** No public project combines all of these.

The competitive risk is not another portfolio project — it's that a
technical reviewer doesn't understand what's unique because the README
is 3 lines and the section titles don't make claims. The positioning
is right; the communication of the positioning needs work.

---

## Phase 4: Synthesis & Next Moves

### Cross-referencing internal findings with landscape position

The audit surfaced 23 internal findings and mapped C2C against 8
comparable projects. The synthesis below identifies which internal
fixes matter *more* because of the competitive landscape, and which
landscape-inspired ideas are worth pursuing.

---

### The central insight

C2C's competitive advantage is the combination of:
1. **Shareable URL** (no login, no install)
2. **CPG domain fluency** (waterfall vocabulary, realistic numbers)
3. **Production data pipeline** (SQL → JSON → validation)
4. **Economist-style narrative** (not a dashboard)

Every next move should either **protect an existing advantage** or
**close a gap that undermines one**. Anything that doesn't connect
to these four pillars is polish, not strategy.

---

### Ranked next moves

Moves are grouped into three tiers based on how they interact with
the competitive position. Within each tier, ordered by
impact-to-effort ratio.

#### Tier 1: Fix now — these undermine the value proposition today

| # | Move | Why it matters (landscape × internal) | Effort |
|---|------|---------------------------------------|--------|
| M1 | **Fix stale og:meta tags** | The #1 differentiator is "a CFO can share this via URL." The link preview shows wrong numbers ("fifty-one cents", "$31.8M"). This undermines the core competitive advantage on every LinkedIn share. | 5 min |
| M2 | **Upgrade section titles from descriptive to claim-making** | FT annotation discipline says claim-making titles get stronger reactions. The headline is excellent; the section titles ("Where the Money Goes", "Time Is Money (Literally)") are generic. "Time Is Money" is a cliché — the Economist voice rules explicitly prohibit this. | 15 min |
| M3 | **Make hardcoded prose data-driven** | The data pipeline (advantage #3) is rigorous — 17 reconciliation checks. But the English prose bypasses it entirely, hardcoding retailer names, day counts, and category counts. A technical reviewer who notices this sees a gap between "traceable data" and "untraceable prose." | 30 min |
| M4 | **Update PLAN.md — check off completed tasks** | Anyone reading the repo sees tasks marked incomplete that are clearly done and deployed. Confusing and sloppy. | 2 min |

**Tier 1 total: ~52 minutes.** All of these should be done before
sharing the portfolio piece anywhere.

---

#### Tier 2: Fix soon — strengthens portfolio-readiness for scrutiny

| # | Move | Why it matters (landscape × internal) | Effort |
|---|------|---------------------------------------|--------|
| M5 | **Write a real README** | The landscape scan found C2C occupies a unique niche — but a 3-line README means a GitHub visitor can't see it. The repo is part of the portfolio. It should communicate: what this is, live URL, screenshot, how to build, data pipeline overview, tech stack. This is the #1 "communication of positioning" fix. | 30 min |
| M6 | **Add chart accessibility (aria-labels)** | Major data journalism outlets (the closest quality comparable) do accessibility. C2C claims to "respect the reader's intelligence" — but a screen reader user gets nothing. A technical reviewer at a company that values accessibility would notice. | 15 min |
| M7 | **Add error boundary** | One malformed data point crashes the entire page. For a portfolio piece, a white screen is worse than a degraded chart. | 15 min |
| M8 | **Add requirements.txt** | A reviewer who clones the repo and tries to run the pipeline hits an immediate wall. Five minutes to fix, removes a friction point that creates a bad first impression. | 5 min |
| M9 | **Remove unused deduction_mix from JSON** | Dead payload shipped to every visitor. Either build the UI that uses it or remove it from the export. Leaving it says "unfinished work" to anyone who inspects the network tab. | 10 min |
| M10 | **Add CY2025 subset validation** | Cross-project validation is listed as a unique strength. But it has a hole: the CY2025 filter that produces the actual displayed numbers isn't validated. Closing this hole strengthens a competitive advantage. | 30 min |

**Tier 2 total: ~1 hour 45 minutes.**

---

#### Tier 3: Consider for next arc — feature additions, not fixes

| # | Move | Why it matters | Effort | Recommendation |
|---|------|---------------|--------|----------------|
| M11 | **Add CI/CD pipeline** | Prevents shipping broken TypeScript. Not urgent for a solo project but adds professionalism signal. | 20 min | Do if doing M5 (README mentions "how to contribute") |
| M12 | **Strengthen section titles further with data annotations** | FT-style inline annotations on charts (callout lines pointing to specific bars with context). Deepens the claim-making approach from M2. | 1-2 hr | Consider after M2 ships and you see the result |
| M13 | **Scroll-triggered narrative reveal** | Data journalism's strongest technique. Each deduction stage appears as the reader scrolls, making the leak feel like a progressive discovery. Would require adding Intersection Observer or a scroll library. | 3-4 hr | Best ROI if the piece gets serious LinkedIn traction |
| M14 | **"Bring your own numbers" mode** | NYT calculator pattern — let a CFO input their own gross revenue and see the waterfall recalculate. Transforms from "look at this" to "this is you." | 4-6 hr | Out of scope for this arc per PLAN.md |
| M15 | **Lighthouse audit + performance baseline** | Record a score, optimize if needed. Low urgency (static site is inherently fast). | 30 min | Do during M5 (include score in README) |

---

### What NOT to do

Based on the audit, these are things that might seem tempting but
would not improve the competitive position:

- **Don't add a Sankey chart.** DECISIONS.md explicitly differentiates
  C2C (waterfall) from RDR (Sankey). SankeyArt's critique is noted but
  the positioning decision is sound.
- **Don't add dashboard features** (filters, date pickers, drill-down).
  R10 says narrative, not dashboard. Every vendor tool is a dashboard.
  The differentiation is being a narrative.
- **Don't refactor the chart components** to share TEAL_SCALE or
  formatDollars. The duplication is real (F5, F6) but low-leverage.
  Three files with the same 8-element array is not a maintenance
  burden for a 10-file project.
- **Don't add ESLint/Prettier.** TypeScript strict mode is already on.
  Formatting config adds process without improving the piece.
- **Don't build the deduction_mix UI** unless it serves the narrative.
  The data exists but "more charts" doesn't make the story better.
  Remove the data (M9) unless there's a clear narrative use.

---

### Suggested execution order

```
Session 1 (quick — ~1 hour):
  M1  Fix og:meta tags                    5 min
  M2  Claim-making section titles         15 min
  M3  Data-driven prose                   30 min
  M4  Update PLAN.md                      2 min
  M8  Add requirements.txt                5 min
  → Deploy, verify link preview

Session 2 (polish — ~1.5 hours):
  M5  Write README                        30 min
  M6  Chart accessibility                 15 min
  M7  Error boundary                      15 min
  M9  Remove unused deduction_mix         10 min
  M10 CY2025 validation                   30 min
  → Deploy, commit, /wrap

Session 3 (optional — future arc):
  M11-M15 as appropriate
```

---

### Final assessment

**Project grade: B+**

The story works. The data pipeline is solid. The positioning is
unique. The deployment is live. For a portfolio piece built in ~2
days, this is strong work.

What separates it from an A is communication: stale metadata,
generic section titles, a minimal README, and accessibility gaps.
These are all fixable in ~2.5 hours of focused work (Sessions 1-2
above).

The project does not need more features. It needs the features it
has to be communicated at the same quality level as the data
engineering behind them.
