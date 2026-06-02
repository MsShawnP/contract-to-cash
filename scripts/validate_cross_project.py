"""Cross-project reconciliation validation for Contract-to-Cash.

Verifies that C2C's view of the data matches all other Cinderhaven
projects' published canonical figures. Exits 0 on success, 1 on any
mismatch.

Canonical values from:
  - retailer-deduction-recovery summary.json
  - short-ship-cost data
  - trade-spend-data-diagnostic

Usage:
    DATABASE_URL=postgresql://... python scripts/validate_cross_project.py
"""

from __future__ import annotations

import sys

from db import connect


def main():
    checks = []
    failures = []

    def check(name, expected, actual, tolerance=0.01):
        """Register a check. Tolerance is relative (0.01 = 1%)."""
        passed = True
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if expected == 0:
                passed = actual == 0
            else:
                passed = abs(actual - expected) / abs(expected) <= tolerance
        else:
            passed = actual == expected

        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            print(f"         Expected: {expected}")
            print(f"         Actual:   {actual}")
            failures.append((name, expected, actual))
        checks.append((name, passed))

    print("=" * 60, flush=True)
    print("  CROSS-PROJECT RECONCILIATION VALIDATION")
    print("=" * 60)

    conn = connect()
    cur = conn.cursor()

    # ─── Section 1: Deduction totals (must match RDR) ─────────────────────
    print("\n--- Deductions (vs retailer-deduction-recovery) ---\n", flush=True)

    cur.execute("SELECT COUNT(*) AS n, SUM(deduction_amount) AS total FROM fct_retailer_deductions")
    ded = cur.fetchone()
    check("Deduction count", 3087, ded["n"], tolerance=0)
    check("Deduction total ($)", 1537390.70, ded["total"], tolerance=0.001)

    # Deduction type count.
    cur.execute("SELECT COUNT(DISTINCT deduction_type) AS n FROM fct_retailer_deductions")
    check("Deduction types", 9, cur.fetchone()["n"], tolerance=0)

    # Disputes filed.
    cur.execute("SELECT COUNT(*) AS n FROM fct_retailer_deductions WHERE was_disputed = true")
    check("Disputes filed", 1410, cur.fetchone()["n"], tolerance=0)

    # Recovery amount.
    cur.execute("SELECT SUM(net_recovery) AS total FROM fct_retailer_deductions WHERE net_recovery > 0")
    check("Dispute recovery ($)", 98215.54, cur.fetchone()["total"], tolerance=0.01)

    # ─── Section 2: Order totals ──────────────────────────────────────────
    print("\n--- Orders (vs RDR / platform) ---\n", flush=True)

    cur.execute("""
        SELECT COUNT(DISTINCT order_id) AS n, SUM(line_total) AS total
        FROM fct_retailer_orders WHERE channel = 'B2B'
    """)
    ord_b2b = cur.fetchone()
    check("B2B order count", 5838, ord_b2b["n"], tolerance=0)
    check("B2B invoiced total ($)", 31409072.52, ord_b2b["total"], tolerance=0.001)

    # DTC orders exist.
    cur.execute("SELECT COUNT(DISTINCT order_id) AS n FROM fct_dtc_orders")
    check("DTC order count", 10000, cur.fetchone()["n"], tolerance=0)

    # ─── Section 3: Shipments ─────────────────────────────────────────────
    print("\n--- Shipments ---\n", flush=True)

    cur.execute("SELECT COUNT(*) AS n FROM fct_retailer_shipments")
    check("Shipment count (1:1 with B2B orders)", 5838, cur.fetchone()["n"], tolerance=0)

    # ─── Section 4: Retailers ─────────────────────────────────────────────
    print("\n--- Retailers ---\n", flush=True)

    cur.execute("SELECT COUNT(*) AS n FROM dim_retailers WHERE channel_type != 'dtc'")
    check("B2B retailer count", 9, cur.fetchone()["n"], tolerance=0)

    cur.execute("SELECT COUNT(*) AS n FROM dim_retailers")
    total_retailers = cur.fetchone()["n"]
    check("Total retailer/channel count (9 B2B + DTC)", 10, total_retailers, tolerance=0)

    # ─── Section 5: Payments ──────────────────────────────────────────────
    print("\n--- Payments ---\n", flush=True)

    cur.execute("SELECT SUM(gross_amount) AS gross, SUM(net_amount) AS net FROM fct_retailer_payments")
    pay = cur.fetchone()
    # Payments gross-net difference should match deductions total (approximately).
    implied_deductions = pay["gross"] - pay["net"]
    check(
        "Payments implied deductions ~ deduction total",
        ded["total"],
        implied_deductions,
        tolerance=0.05,
    )

    # ─── Section 6: DTC payment data is additive ──────────────────────────
    print("\n--- DTC additivity (B2B unaffected) ---\n", flush=True)

    # Verify DTC tables exist but don't interfere with B2B queries.
    cur.execute("SELECT COUNT(*) AS n FROM raw.shopify_transactions")
    dtc_txn = cur.fetchone()["n"]
    check("DTC transactions exist", True, dtc_txn > 0, tolerance=0)

    # B2B deduction total unchanged (no DTC deductions mixed in).
    cur.execute("""
        SELECT SUM(deduction_amount) AS total FROM fct_retailer_deductions
    """)
    check(
        "Deductions still B2B-only after DTC synthesis",
        1537390.70,
        cur.fetchone()["total"],
        tolerance=0.001,
    )

    # B2B order total unchanged.
    cur.execute("""
        SELECT SUM(line_total) AS total FROM fct_retailer_orders WHERE channel = 'B2B'
    """)
    check(
        "B2B order total unchanged after DTC synthesis",
        31409072.52,
        cur.fetchone()["total"],
        tolerance=0.001,
    )

    # ─── Section 7: DTC payment integrity ─────────────────────────────────
    print("\n--- DTC payment internal consistency ---\n", flush=True)

    cur.execute("""
        SELECT
            SUM(order_amount) AS gross,
            SUM(processing_fee) AS fees,
            SUM(net_amount) AS net
        FROM raw.shopify_transactions
    """)
    dtc = cur.fetchone()
    check(
        "DTC: gross - fees = net",
        round(dtc["gross"] - dtc["fees"], 2),
        round(dtc["net"], 2),
        tolerance=0.001,
    )

    cur.execute("SELECT SUM(refund_amount) AS total FROM raw.shopify_refunds")
    dtc_refunds = cur.fetchone()["total"]

    cur.execute("""
        SELECT SUM(chargeback_amount) AS amt, SUM(chargeback_fee) AS fees
        FROM raw.shopify_chargebacks WHERE outcome = 'lost'
    """)
    cb = cur.fetchone()
    dtc_cb_lost = (cb["amt"] or 0) + (cb["fees"] or 0)

    total_dtc_leakage = dtc["fees"] + dtc_refunds + dtc_cb_lost
    dtc_leakage_pct = total_dtc_leakage / dtc["gross"] * 100
    check("DTC leakage rate realistic (5-10%)", True, 5 <= dtc_leakage_pct <= 10, tolerance=0)

    # ─── Results ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    total = len(checks)
    passed = sum(1 for _, p in checks if p)
    failed = total - passed

    if failed == 0:
        print(f"  ALL {total} CHECKS PASSED")
        print("=" * 60)
        conn.close()
        sys.exit(0)
    else:
        print(f"  {failed} of {total} CHECKS FAILED:")
        for name, expected, actual in failures:
            print(f"    - {name}: expected {expected}, got {actual}")
        print("=" * 60)
        conn.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
