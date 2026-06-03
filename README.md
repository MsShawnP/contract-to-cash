# Contract to Cash

Revenue lifecycle analysis for a mid-market CPG brand — tracing where money leaks between invoice and cash receipt. For every dollar Cinderhaven Foods invoiced in Calendar Year 2025, eighty-six cents arrived as cash.

**Live:** https://cash.lailarallc.com

## What this is

A single-page narrative that answers the question a $25M CPG brand's CFO cannot: *On that deal we signed in Q1 — what did we actually net, and where did the money leak between systems?*

The piece traces $17.8M invoiced across 6 retail partners and a DTC channel through deductions, processing fees, refunds, and timing delays. Three charts tell the story:

1. **Waterfall** — gross B2B payments descending through 10 deduction categories to net received
2. **Retailer comparison** — leakage rates from 11.8% to 12.9% across 6 direct retail partners
3. **Time-to-cash** — average days from order to payment, ranging 22–29 days by retailer

Economist-style visual language: minimal gridlines, text labels on every data point, no decoration. Written in sober, declarative prose.

## Architecture

```
Cinderhaven Data Platform (Postgres)
    │
    ├─ scripts/export_json.py ──→ frontend/public/json/ (3 static JSON files)
    │
    └─ scripts/validate_*.py ──→ 49 reconciliation + consistency checks
                                    (17 cross-project, 32 exported JSON)

frontend/ (React SPA)
    ├─ Vite + TypeScript + Recharts
    ├─ Self-hosted fonts (Playfair Display, Source Sans 3)
    └─ Deployed to Cloudflare Workers
```

All figures in the SPA trace to specific SQL queries in `scripts/export_json.py`. Two validation scripts verify data integrity:

- `validate_cross_project.py` — 17 checks against canonical Cinderhaven platform numbers
- `validate_exported_json.py` — 32 checks on the CY2025-scoped JSON the SPA displays

## Data pipeline

The SPA consumes pre-aggregated static JSON. No runtime database connection.

| Script | Purpose |
|--------|---------|
| `scripts/explore_lifecycle.py` | Exploration queries (discovery phase) |
| `scripts/generate_dtc_payments.py` | Synthesize Shopify payment data for DTC orders |
| `scripts/export_json.py` | Production export: Postgres → JSON (CY2025, retailers only) |
| `scripts/validate_cross_project.py` | Reconciliation against other Cinderhaven projects |
| `scripts/validate_exported_json.py` | Internal consistency of exported JSON |

## Running locally

**Frontend:**

```sh
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`.

**Python scripts** (require Cinderhaven Postgres access):

```sh
pip install -r scripts/requirements.txt
DATABASE_URL=postgresql://... python scripts/export_json.py
python scripts/validate_exported_json.py
```

**Deploy:**

```sh
cd frontend
npm run deploy
```

## Tech stack

- **Frontend:** React 19, TypeScript 6, Vite 8, Recharts 2.15
- **Deployment:** Cloudflare Workers (static assets, SPA routing)
- **Data pipeline:** Python 3, psycopg2, Cinderhaven Data Platform (Postgres)
- **Design system:** Lailara Design System (self-hosted fonts, teal palette, Economist chart rules)

## Part of the Cinderhaven portfolio

This is the second buyer-facing project built on the Cinderhaven Data Platform. It tells the full revenue lifecycle story — differentiated from [Retailer Deduction Recovery](https://github.com/MsShawnP/retailer-deduction-recovery), which covers deduction recovery in depth.

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
