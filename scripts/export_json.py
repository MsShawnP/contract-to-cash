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
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extensions
import psycopg2.extras

DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "frontend" / "public" / "json"


def connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.cursor().execute("SET search_path TO public_marts, raw, public")
    conn.commit()
    return conn


def write_json(filename, data, indent=2):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)
    print(f"  Wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)", flush=True)


def export_summary(cur):
    """Top-line metrics for the hero section."""
    print("\n--- summary.json ---", flush=True)

    # B2B payments.
    cur.execute("""
        SELECT
            SUM(gross_amount) AS b2b_gross,
            SUM(net_amount) AS b2b_net,
            COUNT(*) AS remittance_count
        FROM fct_payments
    """)
    pay = cur.fetchone()

    # B2B invoiced.
    cur.execute("""
        SELECT SUM(line_total) AS total FROM fct_orders WHERE channel = 'B2B'
    """)
    b2b_invoiced = cur.fetchone()["total"]

    # B2B deductions.
    cur.execute("""
        SELECT COUNT(*) AS n, SUM(deduction_amount) AS total,
               SUM(net_recovery) AS recovered
        FROM fct_deductions
    """)
    ded = cur.fetchone()

    # DTC.
    cur.execute("""
        SELECT
            SUM(order_amount) AS gross,
            SUM(processing_fee) AS fees,
            SUM(net_amount) AS net
        FROM raw.shopify_transactions
    """)
    dtc_txn = cur.fetchone()

    cur.execute("SELECT SUM(refund_amount) AS total FROM raw.shopify_refunds")
    dtc_refunds = cur.fetchone()["total"]

    cur.execute("""
        SELECT SUM(chargeback_amount + chargeback_fee) AS total
        FROM raw.shopify_chargebacks WHERE outcome = 'lost'
    """)
    dtc_cb = cur.fetchone()["total"] or 0

    dtc_leakage = dtc_txn["fees"] + dtc_refunds + dtc_cb
    dtc_net = dtc_txn["gross"] - dtc_leakage

    # Combined.
    combined_invoiced = b2b_invoiced + dtc_txn["gross"]
    combined_net = pay["b2b_net"] + dtc_net
    combined_leakage = (pay["b2b_gross"] - pay["b2b_net"]) + dtc_leakage

    summary = {
        "headline": "For Every Dollar Invoiced, Fifty-One Cents Arrives as Cash",
        "headline_ratio": round(combined_net / combined_invoiced, 3),
        "b2b": {
            "invoiced": round(b2b_invoiced, 2),
            "gross_payments": round(pay["b2b_gross"], 2),
            "net_received": round(pay["b2b_net"], 2),
            "total_deductions": round(ded["total"], 2),
            "deduction_count": ded["n"],
            "recovered": round(ded["recovered"], 2),
            "leakage_pct": round((pay["b2b_gross"] - pay["b2b_net"]) / pay["b2b_gross"] * 100, 1),
            "remittance_count": pay["remittance_count"],
        },
        "dtc": {
            "gross": round(dtc_txn["gross"], 2),
            "processing_fees": round(dtc_txn["fees"], 2),
            "refunds": round(dtc_refunds, 2),
            "chargebacks_lost": round(dtc_cb, 2),
            "net_received": round(dtc_net, 2),
            "leakage_pct": round(dtc_leakage / dtc_txn["gross"] * 100, 1),
        },
        "combined": {
            "total_invoiced": round(combined_invoiced, 2),
            "total_net": round(combined_net, 2),
            "total_leakage": round(combined_leakage, 2),
            "cents_per_dollar": round(combined_net / combined_invoiced * 100, 1),
        },
        "meta": {
            "retailers_b2b": 10,
            "retailers_total": 11,
            "orders_b2b": 5838,
            "orders_dtc": 10000,
            "skus": 90,
            "time_window": "Dec 2024 - May 2026",
        },
    }

    write_json("summary.json", summary)
    return summary


def export_lifecycle(cur):
    """Waterfall stages — deduction type breakdown for the anchor chart."""
    print("\n--- lifecycle.json ---", flush=True)

    # B2B waterfall: gross → each deduction type → net.
    cur.execute("SELECT SUM(gross_amount) AS gross FROM fct_payments")
    b2b_gross = cur.fetchone()["gross"]

    cur.execute("""
        SELECT deduction_type, COUNT(*) AS count,
               SUM(deduction_amount) AS amount,
               SUM(net_recovery) AS recovered
        FROM fct_deductions
        GROUP BY deduction_type
        ORDER BY SUM(deduction_amount) DESC
    """)
    deduction_stages = []
    for row in cur.fetchall():
        deduction_stages.append({
            "stage": row["deduction_type"],
            "label": row["deduction_type"].replace("_", " ").title(),
            "amount": round(row["amount"], 2),
            "count": row["count"],
            "recovered": round(row["recovered"], 2),
        })

    cur.execute("SELECT SUM(net_amount) AS net FROM fct_payments")
    b2b_net = cur.fetchone()["net"]

    # DTC waterfall.
    cur.execute("SELECT SUM(order_amount) AS gross FROM raw.shopify_transactions")
    dtc_gross = cur.fetchone()["gross"]

    cur.execute("SELECT SUM(processing_fee) AS total FROM raw.shopify_transactions")
    dtc_fees = cur.fetchone()["total"]

    cur.execute("SELECT SUM(refund_amount) AS total FROM raw.shopify_refunds")
    dtc_refunds = cur.fetchone()["total"]

    cur.execute("""
        SELECT SUM(chargeback_amount) AS amt, SUM(chargeback_fee) AS fees
        FROM raw.shopify_chargebacks WHERE outcome = 'lost'
    """)
    cb = cur.fetchone()
    dtc_chargebacks = (cb["amt"] or 0) + (cb["fees"] or 0)

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

    # Leakage by retailer.
    cur.execute("""
        SELECT
            p.retailer_name,
            SUM(p.gross_amount) AS gross,
            SUM(p.net_amount) AS net,
            SUM(p.gross_amount) - SUM(p.net_amount) AS leakage,
            COUNT(*) AS remittance_count
        FROM fct_payments p
        GROUP BY p.retailer_name
        ORDER BY SUM(p.gross_amount) - SUM(p.net_amount) DESC
    """)
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

    # Time-to-cash by retailer.
    cur.execute("""
        WITH order_payment AS (
            SELECT
                d.retailer_name,
                (p.received_date - o.order_date) AS days_to_cash
            FROM fct_deductions d
            JOIN fct_orders o ON o.order_id = d.order_id
            JOIN fct_payments p ON p.remittance_id = d.remittance_id
            WHERE o.channel = 'B2B'
              AND o.order_date IS NOT NULL
              AND p.received_date IS NOT NULL
        )
        SELECT
            retailer_name,
            COUNT(*) AS sample_size,
            ROUND(AVG(days_to_cash), 1) AS avg_days,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_to_cash) AS median_days
        FROM order_payment
        GROUP BY retailer_name
        ORDER BY AVG(days_to_cash) DESC
    """)
    time_to_cash = []
    for row in cur.fetchall():
        time_to_cash.append({
            "name": row["retailer_name"],
            "avg_days": float(row["avg_days"]),
            "median_days": float(row["median_days"]),
            "sample_size": row["sample_size"],
        })

    # Top deduction types per retailer.
    cur.execute("""
        SELECT
            retailer_name,
            deduction_type,
            SUM(deduction_amount) AS amount,
            COUNT(*) AS count
        FROM fct_deductions
        GROUP BY retailer_name, deduction_type
        ORDER BY retailer_name, SUM(deduction_amount) DESC
    """)
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
    cur = conn.cursor()

    summary = export_summary(cur)
    lifecycle = export_lifecycle(cur)
    retailers = export_retailers(cur)

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"  Export complete. Files in frontend/public/json/")
    print(f"  Headline ratio: {summary['combined']['cents_per_dollar']}c per dollar")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
