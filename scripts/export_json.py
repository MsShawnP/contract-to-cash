"""Export Contract-to-Cash data to static JSON for the React SPA.

Queries the Cinderhaven Data Platform and produces:
  - summary.json:    headline numbers, total gross-to-net
  - lifecycle.json:  waterfall stages (deduction type breakdown)
  - retailers.json:  per-retailer leakage comparison + time-to-cash

Usage:
    DATABASE_URL=postgresql://... python scripts/export_json.py
"""

from __future__ import annotations

import json
from pathlib import Path

from db import connect

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "frontend" / "public" / "json"

PERIOD_START = "2023-01-01"
PERIOD_END = "2026-01-02"
PERIOD_LABEL = "36 Months (2023–2026)"

ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def num_to_word(n: int) -> str:
    if n == 0:
        return "Zero"
    if n < 20:
        return ONES[n]
    if n >= 100:
        return str(n)
    return f"{TENS[n // 10]}-{ONES[n % 10]}" if n % 10 else TENS[n // 10]


def write_json(filename, data, indent=2):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)
    print(f"  Wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)", flush=True)


def export_summary(cur):
    """Top-line metrics for the hero section."""
    print("\n--- summary.json ---", flush=True)

    # B2B payments (retailers only, within period).
    cur.execute("""
        SELECT
            SUM(p.gross_amount) AS b2b_gross,
            SUM(p.net_amount) AS b2b_net,
            COUNT(*) AS remittance_count
        FROM fct_retailer_payments p
        WHERE p.received_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    pay = cur.fetchone()

    # B2B invoiced (retailers only, within period). Use line_total on the
    # channel='B2B' orders — the same measure the cross-project canonical uses
    # (validate_cross_project.py). Dropping the channel filter and using
    # total_value erased the invoice-to-collection gap (invoiced == gross_payments).
    cur.execute("""
        SELECT SUM(o.line_total) AS total, COUNT(DISTINCT o.order_id) AS order_count
        FROM fct_retailer_orders o
        WHERE o.channel = 'B2B' AND o.po_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    orders_row = cur.fetchone()
    b2b_invoiced = orders_row["total"]
    b2b_order_count = orders_row["order_count"]

    # B2B deductions (retailers only, within period via payment date).
    # Count DISTINCT deductions whose remittance falls in the period. Joining to
    # fct_retailer_payments fanned each deduction out by the number of payment
    # rows sharing its remittance_id (~4.8x, 3,087 -> ~14,947); the IN-subquery
    # keeps one row per deduction so count and totals are real.
    cur.execute("""
        SELECT COUNT(*) AS n, SUM(d.deduction_amount) AS total,
               SUM(d.recovered_amount) AS recovered
        FROM fct_retailer_deductions d
        WHERE d.remittance_id IN (
            SELECT remittance_id FROM fct_retailer_payments
            WHERE received_date BETWEEN %s AND %s
        )
    """, (PERIOD_START, PERIOD_END))
    ded = cur.fetchone()

    # Retailer count.
    cur.execute("""
        SELECT COUNT(*) AS n FROM dim_retailers
    """)
    retailer_count = cur.fetchone()["n"]

    # DTC (within period).
    cur.execute("""
        SELECT
            SUM(order_amount) AS gross,
            SUM(processing_fee) AS fees,
            SUM(net_amount) AS net
        FROM raw.shopify_transactions
        WHERE transaction_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    dtc_txn = cur.fetchone()

    cur.execute("""
        SELECT SUM(refund_amount) AS total FROM raw.shopify_refunds
        WHERE refund_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    dtc_refunds = cur.fetchone()["total"] or 0

    cur.execute("""
        SELECT SUM(chargeback_amount) AS amount
        FROM raw.shopify_chargebacks
        WHERE outcome = 'lost' AND chargeback_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    cb_row = cur.fetchone()
    dtc_cb = cb_row["amount"] or 0

    dtc_leakage = (dtc_txn["fees"] or 0) + (dtc_refunds or 0) + dtc_cb
    dtc_gross = dtc_txn["gross"] or 0
    dtc_net = dtc_gross - dtc_leakage

    # DTC order count in period.
    cur.execute("""
        SELECT COUNT(DISTINCT order_id) AS n FROM fct_dtc_orders
        WHERE created_at::date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    dtc_order_count = cur.fetchone()["n"]

    # Combined.
    combined_invoiced = b2b_invoiced + dtc_gross
    combined_net = pay["b2b_net"] + dtc_net
    combined_leakage = (pay["b2b_gross"] - pay["b2b_net"]) + dtc_leakage

    headline_ratio = combined_net / combined_invoiced if combined_invoiced else 0
    cents = round(combined_net / combined_invoiced * 100, 1)
    cents_word = num_to_word(int(cents))
    headline = f"For Every Dollar Invoiced, {cents_word} Cents Arrives as Cash"

    summary = {
        "headline": headline,
        "headline_ratio": round(headline_ratio, 3),
        "b2b": {
            "invoiced": round(b2b_invoiced, 2),
            "gross_payments": round(pay["b2b_gross"], 2),
            "net_received": round(pay["b2b_net"], 2),
            "total_deductions": round(ded["total"], 2),
            "deduction_count": ded["n"],
            "recovered": round(ded["recovered"], 2),
            "leakage_pct": round((pay["b2b_gross"] - pay["b2b_net"]) / pay["b2b_gross"] * 100, 1) if pay["b2b_gross"] else 0,
            "remittance_count": pay["remittance_count"],
        },
        "dtc": {
            "gross": round(dtc_gross, 2),
            "processing_fees": round(dtc_txn["fees"] or 0, 2),
            "refunds": round(dtc_refunds, 2),
            "chargebacks_lost": round(dtc_cb, 2),
            "net_received": round(dtc_net, 2),
            "leakage_pct": round(dtc_leakage / dtc_gross * 100, 1) if dtc_gross else 0,
        },
        "combined": {
            "total_invoiced": round(combined_invoiced, 2),
            "total_net": round(combined_net, 2),
            "total_leakage": round(combined_leakage, 2),
            "cents_per_dollar": cents,
        },
        "meta": {
            "retailers_b2b": retailer_count,
            "retailers_total": retailer_count + 1,
            "orders_b2b": b2b_order_count,
            "orders_dtc": dtc_order_count,
            "skus": 50,  # Cinderhaven product catalog size (canonical: seed_config.py)
            "time_window": PERIOD_LABEL,
        },
    }

    write_json("summary.json", summary)
    return summary


def export_lifecycle(cur):
    """Waterfall stages — deduction type breakdown for the anchor chart."""
    print("\n--- lifecycle.json ---", flush=True)

    # B2B waterfall: gross → each deduction type → net (retailers only, within period).
    cur.execute("""
        SELECT SUM(p.gross_amount) AS gross
        FROM fct_retailer_payments p
        WHERE p.received_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    b2b_gross = cur.fetchone()["gross"]

    # One row per deduction (IN-subquery, not a payments JOIN) so per-type
    # counts and amounts are not fanned out by the remittance→payment join.
    cur.execute("""
        SELECT d.deduction_type, COUNT(*) AS count,
               SUM(d.deduction_amount) AS amount,
               SUM(d.recovered_amount) AS recovered
        FROM fct_retailer_deductions d
        WHERE d.remittance_id IN (
            SELECT remittance_id FROM fct_retailer_payments
            WHERE received_date BETWEEN %s AND %s
        )
        GROUP BY d.deduction_type
        ORDER BY SUM(d.deduction_amount) DESC
    """, (PERIOD_START, PERIOD_END))
    deduction_stages = []
    for row in cur.fetchall():
        deduction_stages.append({
            "stage": row["deduction_type"],
            "label": row["deduction_type"].replace("_", " ").title(),
            "amount": round(row["amount"], 2),
            "count": row["count"],
            "recovered": round(row["recovered"] or 0, 2),
        })

    cur.execute("""
        SELECT SUM(p.net_amount) AS net
        FROM fct_retailer_payments p
        WHERE p.received_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    b2b_net = cur.fetchone()["net"]

    # Gross-to-net residual not tied to any itemized deduction record — largely
    # un-itemized trade spend. Emitted as a separate band with count 0 so the
    # frontend reports it as "unreconciled," NOT as a deduction category taking
    # its cut. (It is excluded from summary.total_deductions.)
    categorized = sum(s["amount"] for s in deduction_stages)
    unreconciled = round(b2b_gross - b2b_net - categorized, 2)
    if unreconciled > 0:
        deduction_stages.append({
            "stage": "unreconciled",
            "label": "Unreconciled",
            "amount": unreconciled,
            "count": 0,
            "recovered": 0,
        })

    # DTC waterfall (within period).
    cur.execute("""
        SELECT SUM(order_amount) AS gross, SUM(processing_fee) AS fees
        FROM raw.shopify_transactions
        WHERE transaction_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    dtc_row = cur.fetchone()
    dtc_gross = dtc_row["gross"] or 0
    dtc_fees = dtc_row["fees"] or 0

    cur.execute("""
        SELECT SUM(refund_amount) AS total FROM raw.shopify_refunds
        WHERE refund_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    dtc_refunds = cur.fetchone()["total"] or 0

    cur.execute("""
        SELECT SUM(chargeback_amount) AS amt
        FROM raw.shopify_chargebacks
        WHERE outcome = 'lost' AND chargeback_date BETWEEN %s AND %s
    """, (PERIOD_START, PERIOD_END))
    cb = cur.fetchone()
    dtc_chargebacks = cb["amt"] or 0

    dtc_net = dtc_gross - dtc_fees - dtc_refunds - dtc_chargebacks

    lifecycle = {
        "b2b": {
            "gross": round(b2b_gross, 2),
            "net": round(b2b_net, 2),
            "stages": deduction_stages,
        },
        "dtc": {
            "gross": round(dtc_gross, 2),
            "net": round(dtc_net, 2),
            "stages": [
                {"stage": "processing_fees", "label": "Processing Fees", "amount": round(dtc_fees, 2)},
                {"stage": "refunds", "label": "Refunds", "amount": round(dtc_refunds, 2)},
                {"stage": "chargebacks", "label": "Chargebacks", "amount": round(dtc_chargebacks, 2)},
            ],
        },
    }

    write_json("lifecycle.json", lifecycle)
    return lifecycle


def export_retailers(cur):
    """Per-retailer leakage comparison and time-to-cash."""
    print("\n--- retailers.json ---", flush=True)

    # Leakage by retailer (within period).
    cur.execute("""
        SELECT
            dr.retailer_name,
            SUM(p.gross_amount) AS gross,
            SUM(p.net_amount) AS net,
            SUM(p.gross_amount) - SUM(p.net_amount) AS leakage,
            COUNT(*) AS remittance_count
        FROM fct_retailer_payments p
        JOIN dim_retailers dr ON dr.retailer_id = p.retailer_id
        WHERE p.received_date BETWEEN %s AND %s
        GROUP BY dr.retailer_name
        ORDER BY SUM(p.gross_amount) - SUM(p.net_amount) DESC
    """, (PERIOD_START, PERIOD_END))
    retailer_leakage = []
    for row in cur.fetchall():
        leak_pct = row["leakage"] / row["gross"] * 100 if row["gross"] else 0
        retailer_leakage.append({
            "name": row["retailer_name"],
            "gross": round(row["gross"], 2),
            "net": round(row["net"], 2),
            "leakage": round(row["leakage"], 2),
            "leakage_pct": round(leak_pct, 1),
            "remittances": row["remittance_count"],
        })

    # Time-to-cash by retailer (within period). One row PER ORDER (DISTINCT),
    # dollar-weighted by order value — not one row per deduction, which weighted
    # the average by how many deductions an order incurred. NOTE: orders link to
    # payments only through fct_retailer_deductions in the current schema, so the
    # sample is orders that incurred a deduction; a full-population DSO would need
    # a direct order→payment key.
    cur.execute("""
        WITH order_cash AS (
            SELECT DISTINCT
                d.order_id,
                dr.retailer_name,
                o.line_total AS order_value,
                (p.received_date - o.po_date) AS days_to_cash
            FROM fct_retailer_deductions d
            JOIN fct_retailer_orders o ON o.order_id = d.order_id
            JOIN fct_retailer_payments p ON p.remittance_id = d.remittance_id
            JOIN dim_retailers dr ON dr.retailer_id = d.retailer_id
            WHERE p.received_date BETWEEN %s AND %s
              AND o.po_date IS NOT NULL
        )
        SELECT
            retailer_name,
            COUNT(*) AS sample_size,
            ROUND(
                SUM(days_to_cash * order_value)::numeric
                / NULLIF(SUM(order_value), 0), 1
            ) AS avg_days,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_to_cash) AS median_days
        FROM order_cash
        GROUP BY retailer_name
        ORDER BY avg_days DESC
    """, (PERIOD_START, PERIOD_END))
    time_to_cash = []
    for row in cur.fetchall():
        time_to_cash.append({
            "name": row["retailer_name"],
            "avg_days": float(row["avg_days"]),
            "median_days": float(row["median_days"]),
            "sample_size": row["sample_size"],
        })

    # Top deduction types per retailer (within period).
    cur.execute("""
        SELECT
            dr.retailer_name,
            d.deduction_type,
            SUM(d.deduction_amount) AS amount,
            COUNT(*) AS count
        FROM fct_retailer_deductions d
        JOIN dim_retailers dr ON dr.retailer_id = d.retailer_id
        JOIN fct_retailer_payments p ON p.remittance_id = d.remittance_id
        WHERE p.received_date BETWEEN %s AND %s
        GROUP BY dr.retailer_name, d.deduction_type
        ORDER BY dr.retailer_name, SUM(d.deduction_amount) DESC
    """, (PERIOD_START, PERIOD_END))
    deduction_mix = {}
    for row in cur.fetchall():
        name = row["retailer_name"]
        if name not in deduction_mix:
            deduction_mix[name] = []
        deduction_mix[name].append({
            "type": row["deduction_type"],
            "label": row["deduction_type"].replace("_", " ").title(),
            "amount": round(row["amount"], 2),
            "count": row["count"],
        })

    retailers = {
        "leakage": retailer_leakage,
        "time_to_cash": time_to_cash,
        "deduction_mix": deduction_mix,
    }

    write_json("retailers.json", retailers)
    return retailers


def main():
    print("=" * 60, flush=True)
    print("  CONTRACT-TO-CASH: JSON EXPORT")
    print("=" * 60, flush=True)

    conn = connect()
    try:
        cur = conn.cursor()

        summary = export_summary(cur)
        lifecycle = export_lifecycle(cur)
        retailers = export_retailers(cur)

        print(f"\n{'=' * 60}")
        print(f"  Export complete. Files in frontend/public/json/")
        print(f"  Headline ratio: {summary['combined']['cents_per_dollar']}c per dollar")
        print(f"{'=' * 60}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
