"""Investigate the timing mismatch between orders and payments."""

import os
import psycopg2
import psycopg2.extras

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:REDACTED@localhost:5432/cinderhaven",
)

conn = psycopg2.connect(
    os.environ["DATABASE_URL"],
    cursor_factory=psycopg2.extras.RealDictCursor,
)
cur = conn.cursor()
cur.execute("SET search_path TO public_marts, raw, public")

print("=" * 60)
print("  TIMING & DTC INVESTIGATION")
print("=" * 60)

# --- DTC count mismatch ---
print("\n--- DTC Order Count Mismatch ---\n")

cur.execute("""
    SELECT COUNT(DISTINCT order_id) AS n
    FROM fct_orders WHERE channel = 'DTC'
      AND order_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
print(f"fct_orders DTC CY2025: {cur.fetchone()['n']}")

cur.execute("""
    SELECT COUNT(*) AS n, SUM(order_amount) AS gross, AVG(order_amount) AS aov
    FROM raw.shopify_transactions
    WHERE transaction_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
r = cur.fetchone()
print(f"shopify_transactions CY2025: {r['n']} txns, ${r['gross']:,.2f} gross, ${r['aov']:.2f} AOV")

cur.execute("SELECT COUNT(*) AS n, SUM(order_amount) AS gross FROM raw.shopify_transactions")
r = cur.fetchone()
print(f"shopify_transactions ALL TIME: {r['n']} txns, ${r['gross']:,.2f} gross")

cur.execute("SELECT COUNT(DISTINCT order_id) AS n FROM fct_orders WHERE channel = 'DTC'")
print(f"fct_orders DTC ALL TIME: {cur.fetchone()['n']}")

# --- B2B Timing ---
print("\n--- B2B Invoiced vs Payments (timing gap) ---\n")

cur.execute("""
    SELECT SUM(o.line_total) AS invoiced, COUNT(DISTINCT o.order_id) AS orders
    FROM fct_orders o
    JOIN dim_retailers dr ON dr.retailer_id = o.retailer_id
    WHERE o.channel = 'B2B' AND dr.channel_type = 'retailer'
      AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
r = cur.fetchone()
print(f"B2B invoiced (CY2025 orders): ${r['invoiced']:,.2f} ({r['orders']} orders)")

cur.execute("""
    SELECT SUM(p.gross_amount) AS gross, SUM(p.net_amount) AS net, COUNT(*) AS n
    FROM fct_payments p
    JOIN dim_retailers dr ON dr.retailer_name = p.retailer_name
    WHERE dr.channel_type = 'retailer'
      AND p.received_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
r = cur.fetchone()
print(f"B2B payments received (CY2025): ${r['gross']:,.2f} gross, ${r['net']:,.2f} net ({r['n']} remittances)")
print(f"  --> Payments EXCEED invoiced by ${float(r['gross']) - 16336050.24:,.2f}")

# --- Payment date distribution ---
print("\n--- Payment date distribution ---\n")

cur.execute("""
    SELECT
        EXTRACT(YEAR FROM p.received_date)::int AS yr,
        EXTRACT(QUARTER FROM p.received_date)::int AS q,
        SUM(p.gross_amount) AS gross,
        COUNT(*) AS n
    FROM fct_payments p
    JOIN dim_retailers dr ON dr.retailer_name = p.retailer_name
    WHERE dr.channel_type = 'retailer'
    GROUP BY 1, 2
    ORDER BY 1, 2
""")
for row in cur.fetchall():
    print(f"  {row['yr']} Q{row['q']}: ${row['gross']:,.2f} ({row['n']} remittances)")

# --- Order date distribution ---
print("\n--- Order date distribution ---\n")

cur.execute("""
    SELECT
        EXTRACT(YEAR FROM o.order_date)::int AS yr,
        EXTRACT(QUARTER FROM o.order_date)::int AS q,
        SUM(o.line_total) AS invoiced,
        COUNT(DISTINCT o.order_id) AS n
    FROM fct_orders o
    JOIN dim_retailers dr ON dr.retailer_id = o.retailer_id
    WHERE o.channel = 'B2B' AND dr.channel_type = 'retailer'
    GROUP BY 1, 2
    ORDER BY 1, 2
""")
for row in cur.fetchall():
    print(f"  {row['yr']} Q{row['q']}: ${row['invoiced']:,.2f} ({row['n']} orders)")

# --- Matched cohort: orders placed in CY2025 that have been paid ---
print("\n--- Matched cohort (CY2025 orders -> their payments) ---\n")

cur.execute("""
    WITH cy2025_orders AS (
        SELECT DISTINCT o.order_id, o.line_total
        FROM fct_orders o
        JOIN dim_retailers dr ON dr.retailer_id = o.retailer_id
        WHERE o.channel = 'B2B' AND dr.channel_type = 'retailer'
          AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
    ),
    linked_payments AS (
        SELECT DISTINCT d.order_id, p.remittance_id, p.gross_amount, p.net_amount
        FROM fct_deductions d
        JOIN fct_payments p ON p.remittance_id = d.remittance_id
        WHERE d.order_id IN (SELECT order_id FROM cy2025_orders)
    )
    SELECT
        (SELECT COUNT(*) FROM cy2025_orders) AS total_orders,
        (SELECT SUM(line_total) FROM cy2025_orders) AS total_invoiced,
        COUNT(DISTINCT lp.order_id) AS orders_with_payments,
        COUNT(DISTINCT lp.remittance_id) AS unique_remittances,
        SUM(lp.gross_amount) AS gross_collected,
        SUM(lp.net_amount) AS net_collected
    FROM linked_payments lp
""")
r = cur.fetchone()
print(f"CY2025 orders: {r['total_orders']}, invoiced ${r['total_invoiced']:,.2f}")
print(f"Of those, {r['orders_with_payments']} have linked payments")
print(f"Those payments: ${r['gross_collected']:,.2f} gross, ${r['net_collected']:,.2f} net")
print(f"Orders without payment link: {r['total_orders'] - r['orders_with_payments']}")

# --- Alternative: all orders that GENERATED CY2025 payments ---
print("\n--- Reverse: orders behind CY2025 payments ---\n")

cur.execute("""
    WITH cy2025_payments AS (
        SELECT p.remittance_id, p.gross_amount, p.net_amount
        FROM fct_payments p
        JOIN dim_retailers dr ON dr.retailer_name = p.retailer_name
        WHERE dr.channel_type = 'retailer'
          AND p.received_date BETWEEN '2025-01-01' AND '2025-12-31'
    ),
    linked_orders AS (
        SELECT DISTINCT d.order_id
        FROM fct_deductions d
        WHERE d.remittance_id IN (SELECT remittance_id FROM cy2025_payments)
    )
    SELECT
        (SELECT COUNT(*) FROM linked_orders) AS orders_behind_cy25_payments,
        (SELECT SUM(line_total) FROM fct_orders WHERE order_id IN (SELECT order_id FROM linked_orders)) AS invoiced_for_those_orders
    FROM (SELECT 1) x
""")
r = cur.fetchone()
print(f"Orders behind CY2025 payments: {r['orders_behind_cy25_payments']}")
print(f"Total invoiced for those orders: ${r['invoiced_for_those_orders']:,.2f}")

conn.close()
