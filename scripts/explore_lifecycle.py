"""Explore the B2B revenue lifecycle in the Cinderhaven Data Platform.

Queries fct_retailer_payments, fct_retailer_deductions, fct_retailer_orders, and fct_retailer_shipments to
calculate the full gross-to-net waterfall, identify leakage by stage and
retailer, and determine whether the data tells a dramatic story.

Output: structured console report for human review.
"""

from __future__ import annotations

from db import connect


def fmt_dollars(n):
    if n is None:
        return "$0"
    if abs(n) >= 1_000_000:
        return f"${n / 1_000_000:,.2f}M"
    if abs(n) >= 1_000:
        return f"${n / 1_000:,.1f}K"
    return f"${n:,.2f}"


def fmt_pct(part, whole):
    if whole == 0:
        return "0.0%"
    return f"{part / whole * 100:.1f}%"


def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def run():
    conn = connect()
    cur = conn.cursor()

    # ─── 1. Aggregate B2B gross-to-net from payments ───────────────────────
    section("1. AGGREGATE B2B GROSS-TO-NET (from fct_retailer_payments)")

    cur.execute("""
        SELECT
            COUNT(*) AS remittance_count,
            SUM(gross_amount) AS total_gross,
            SUM(net_amount) AS total_net,
            SUM(gross_amount) - SUM(net_amount) AS total_leakage,
            MIN(received_date) AS earliest_payment,
            MAX(received_date) AS latest_payment
        FROM fct_retailer_payments
    """)
    payments = cur.fetchone()
    print(f"  Remittances:      {payments['remittance_count']:,}")
    print(f"  Gross received:   {fmt_dollars(payments['total_gross'])}")
    print(f"  Net received:     {fmt_dollars(payments['total_net'])}")
    print(f"  Total leakage:    {fmt_dollars(payments['total_leakage'])} "
          f"({fmt_pct(payments['total_leakage'], payments['total_gross'])})")
    print(f"  Window:           {payments['earliest_payment']} to {payments['latest_payment']}")

    # ─── 2. B2B orders (invoice side) ─────────────────────────────────────
    section("2. B2B ORDERS (invoice measure)")

    cur.execute("""
        SELECT
            COUNT(DISTINCT order_id) AS order_count,
            COUNT(*) AS line_count,
            SUM(line_total) AS total_invoiced
        FROM fct_retailer_orders
        WHERE channel = 'B2B'
    """)
    orders = cur.fetchone()
    print(f"  Distinct orders:  {orders['order_count']:,}")
    print(f"  Line items:       {orders['line_count']:,}")
    print(f"  Total invoiced:   {fmt_dollars(orders['total_invoiced'])}")

    # ─── 3. Deduction breakdown by type ───────────────────────────────────
    section("3. DEDUCTION BREAKDOWN BY TYPE")

    cur.execute("""
        SELECT
            deduction_type,
            COUNT(*) AS count,
            SUM(deduction_amount) AS total_amount,
            SUM(net_recovery) AS total_recovered,
            SUM(net_loss) AS total_net_loss
        FROM fct_retailer_deductions
        GROUP BY deduction_type
        ORDER BY total_amount DESC
    """)
    deduction_types = cur.fetchall()

    total_deductions = sum(r["total_amount"] for r in deduction_types)
    total_count = sum(r["count"] for r in deduction_types)
    print(f"  {'Type':<30} {'Count':>7} {'Amount':>14} {'Recovered':>12} {'Net Loss':>14} {'Share':>7}")
    print(f"  {'-' * 30} {'-' * 7} {'-' * 14} {'-' * 12} {'-' * 14} {'-' * 7}")
    for r in deduction_types:
        print(f"  {r['deduction_type']:<30} {r['count']:>7,} "
              f"{fmt_dollars(r['total_amount']):>14} "
              f"{fmt_dollars(r['total_recovered']):>12} "
              f"{fmt_dollars(r['total_net_loss']):>14} "
              f"{fmt_pct(r['total_amount'], total_deductions):>7}")
    print(f"\n  TOTAL: {total_count:,} deductions = {fmt_dollars(total_deductions)}")

    # ─── 4. Leakage by retailer ───────────────────────────────────────────
    section("4. LEAKAGE BY RETAILER")

    cur.execute("""
        SELECT
            p.retailer_name,
            COUNT(*) AS remittance_count,
            SUM(p.gross_amount) AS gross,
            SUM(p.net_amount) AS net,
            SUM(p.gross_amount) - SUM(p.net_amount) AS leakage
        FROM fct_retailer_payments p
        GROUP BY p.retailer_name
        ORDER BY leakage DESC
    """)
    retailer_payments = cur.fetchall()

    print(f"  {'Retailer':<25} {'Remit#':>6} {'Gross':>14} {'Net':>14} {'Leakage':>14} {'Leak%':>7}")
    print(f"  {'-' * 25} {'-' * 6} {'-' * 14} {'-' * 14} {'-' * 14} {'-' * 7}")
    for r in retailer_payments:
        print(f"  {r['retailer_name']:<25} {r['remittance_count']:>6,} "
              f"{fmt_dollars(r['gross']):>14} "
              f"{fmt_dollars(r['net']):>14} "
              f"{fmt_dollars(r['leakage']):>14} "
              f"{fmt_pct(r['leakage'], r['gross']):>7}")

    # ─── 5. Deduction types by retailer (top 5 retailers) ────────────────
    section("5. DEDUCTION MIX — TOP 5 RETAILERS BY LEAKAGE")

    top_retailers = [r["retailer_name"] for r in retailer_payments[:5]]
    cur.execute("""
        SELECT
            retailer_name,
            deduction_type,
            COUNT(*) AS count,
            SUM(deduction_amount) AS total_amount
        FROM fct_retailer_deductions
        WHERE retailer_name = ANY(%s)
        GROUP BY retailer_name, deduction_type
        ORDER BY retailer_name, total_amount DESC
    """, (top_retailers,))
    retailer_deductions = cur.fetchall()

    current_retailer = None
    for r in retailer_deductions:
        if r["retailer_name"] != current_retailer:
            current_retailer = r["retailer_name"]
            print(f"\n  [{current_retailer}]")
        print(f"    {r['deduction_type']:<28} {r['count']:>5,} = {fmt_dollars(r['total_amount'])}")

    # ─── 6. Time-to-cash by retailer ─────────────────────────────────────
    section("6. TIME-TO-CASH BY RETAILER (avg days: order -> payment received)")

    cur.execute("""
        WITH order_payment AS (
            SELECT
                d.retailer_name,
                o.order_date,
                p.received_date,
                (p.received_date - o.order_date) AS days_to_cash
            FROM fct_retailer_deductions d
            JOIN fct_retailer_orders o ON o.order_id = d.order_id
            JOIN fct_retailer_payments p ON p.remittance_id = d.remittance_id
            WHERE o.channel = 'B2B'
              AND o.order_date IS NOT NULL
              AND p.received_date IS NOT NULL
        )
        SELECT
            retailer_name,
            COUNT(*) AS sample_size,
            AVG(days_to_cash) AS avg_days,
            MIN(days_to_cash) AS min_days,
            MAX(days_to_cash) AS max_days,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_to_cash) AS median_days
        FROM order_payment
        GROUP BY retailer_name
        ORDER BY avg_days DESC
    """)
    time_to_cash = cur.fetchall()

    print(f"  {'Retailer':<25} {'N':>6} {'Avg':>7} {'Med':>7} {'Min':>5} {'Max':>5}")
    print(f"  {'-' * 25} {'-' * 6} {'-' * 7} {'-' * 7} {'-' * 5} {'-' * 5}")
    for r in time_to_cash:
        print(f"  {r['retailer_name']:<25} {r['sample_size']:>6,} "
              f"{r['avg_days']:>7.1f} "
              f"{r['median_days']:>7.1f} "
              f"{r['min_days']:>5} "
              f"{r['max_days']:>5}")

    # ─── 7. Orders with NO deductions (clean payments) ────────────────────
    section("7. ORDERS WITHOUT DEDUCTIONS (clean pass-through)")

    cur.execute("""
        SELECT
            COUNT(DISTINCT o.order_id) AS total_b2b_orders,
            COUNT(DISTINCT d.order_id) AS orders_with_deductions
        FROM fct_retailer_orders o
        LEFT JOIN fct_retailer_deductions d ON d.order_id = o.order_id
        WHERE o.channel = 'B2B'
    """)
    clean = cur.fetchone()
    clean_orders = clean["total_b2b_orders"] - clean["orders_with_deductions"]
    print(f"  Total B2B orders:          {clean['total_b2b_orders']:,}")
    print(f"  Orders with deductions:    {clean['orders_with_deductions']:,}")
    print(f"  Clean orders (no deduct):  {clean_orders:,} "
          f"({fmt_pct(clean_orders, clean['total_b2b_orders'])})")

    # ─── 8. Deductions without order linkage ──────────────────────────────
    section("8. DEDUCTIONS WITHOUT ORDER LINKAGE")

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(deduction_amount) AS total_amount,
            COUNT(*) FILTER (WHERE order_id IS NULL) AS no_order,
            SUM(deduction_amount) FILTER (WHERE order_id IS NULL) AS no_order_amount
        FROM fct_retailer_deductions
    """)
    unlinked = cur.fetchone()
    print(f"  Total deductions:          {unlinked['total']:,}")
    print(f"  Without order_id:          {unlinked['no_order']:,} "
          f"({fmt_pct(unlinked['no_order'], unlinked['total'])})")
    print(f"  Unlinked amount:           {fmt_dollars(unlinked['no_order_amount'])}")

    # ─── 9. Shipment-level signals (short-ships, late deliveries) ─────────
    section("9. SHIPMENT ISSUES (potential leakage signals)")

    cur.execute("""
        SELECT
            COUNT(*) AS total_shipments,
            COUNT(*) FILTER (WHERE NOT clean_delivery) AS not_clean,
            COUNT(*) FILTER (WHERE NOT asn_compliant) AS asn_noncompliant,
            COUNT(*) FILTER (WHERE transit_days > 7) AS slow_transit
        FROM fct_retailer_shipments
    """)
    ship = cur.fetchone()
    print(f"  Total shipments:           {ship['total_shipments']:,}")
    print(f"  Not clean delivery:        {ship['not_clean']:,} "
          f"({fmt_pct(ship['not_clean'], ship['total_shipments'])})")
    print(f"  ASN non-compliant:         {ship['asn_noncompliant']:,} "
          f"({fmt_pct(ship['asn_noncompliant'], ship['total_shipments'])})")
    print(f"  Slow transit (>7 days):    {ship['slow_transit']:,} "
          f"({fmt_pct(ship['slow_transit'], ship['total_shipments'])})")

    # ─── 10. Summary: The story potential ─────────────────────────────────
    section("10. STORY POTENTIAL SUMMARY")

    gross = payments["total_gross"]
    net = payments["total_net"]
    leakage = payments["total_leakage"]
    invoiced = orders["total_invoiced"]

    print(f"  Invoice-to-payment gap:    {fmt_dollars(invoiced - gross)}")
    print(f"    (invoiced {fmt_dollars(invoiced)} vs gross payments {fmt_dollars(gross)})")
    print(f"    This gap = orders not yet paid, timing differences, etc.")
    print()
    print(f"  Payment-level leakage:     {fmt_dollars(leakage)} ({fmt_pct(leakage, gross)} of gross)")
    print(f"    This is confirmed money taken from what retailers owed.")
    print()
    print(f"  Retailer variation (by leakage %):")
    if retailer_payments:
        by_pct = sorted(
            retailer_payments,
            key=lambda r: r["leakage"] / r["gross"] if r["gross"] else 0,
            reverse=True,
        )
        worst = by_pct[0]
        best = by_pct[-1]
        worst_pct = worst["leakage"] / worst["gross"] * 100 if worst["gross"] else 0
        best_pct = best["leakage"] / best["gross"] * 100 if best["gross"] else 0
        print(f"    Worst: {worst['retailer_name']} at {worst_pct:.1f}% leakage")
        print(f"    Best:  {best['retailer_name']} at {best_pct:.1f}% leakage")
        print(f"    Spread: {worst_pct - best_pct:.1f} percentage points")
    print()
    print(f"  Total deductions:          {total_count:,} at {fmt_dollars(total_deductions)}")
    print(f"  Canonical check:           expect 3,087 at $1,537,390.70")
    print(f"  Match: {'YES' if total_count == 3087 else 'NO — INVESTIGATE'}")

    conn.close()
    print("\n" + "=" * 70)
    print("  EXPLORATION COMPLETE — review findings above for story potential")
    print("=" * 70)


if __name__ == "__main__":
    run()
