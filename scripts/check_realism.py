"""Quick realism check on the dataset."""
import os
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    os.environ["DATABASE_URL"],
    cursor_factory=psycopg2.extras.RealDictCursor,
)
cur = conn.cursor()
cur.execute("SET search_path TO public_marts, raw, public")

# B2B: What % of orders have deductions?
cur.execute("""
    SELECT
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT d.order_id) AS orders_with_deductions
    FROM fct_orders o
    JOIN dim_retailers dr ON dr.retailer_id = o.retailer_id
    LEFT JOIN fct_deductions d ON d.order_id = o.order_id
    WHERE o.channel = 'B2B' AND dr.channel_type = 'retailer'
      AND o.order_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
r = cur.fetchone()
print(f"B2B orders in CY2025: {r['total_orders']:,}")
print(f"Orders with deductions: {r['orders_with_deductions']:,} ({r['orders_with_deductions']/r['total_orders']*100:.1f}%)")

# Deduction stats
cur.execute("""
    SELECT COUNT(*) AS n, SUM(deduction_amount) AS total
    FROM fct_deductions d
    JOIN dim_retailers dr ON dr.retailer_name = d.retailer_name
    JOIN fct_payments p ON p.remittance_id = d.remittance_id
    WHERE dr.channel_type = 'retailer'
      AND p.received_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
ded = cur.fetchone()
print(f"Deductions in period: {ded['n']:,} (avg ${float(ded['total'])/ded['n']:.2f} each)")
print(f"Deductions per order: {ded['n']/r['total_orders']:.2f}")

# DTC metrics
cur.execute("""
    SELECT COUNT(*) AS txns, SUM(order_amount) AS gross, AVG(order_amount) AS avg_order
    FROM raw.shopify_transactions
    WHERE transaction_date BETWEEN '2025-01-01' AND '2025-12-31'
""")
dtc = cur.fetchone()
print(f"\nDTC transactions CY2025: {dtc['txns']:,}")
print(f"DTC gross: ${float(dtc['gross']):,.2f}")
print(f"DTC avg order: ${float(dtc['avg_order']):.2f}")

b2b_invoiced = 15267699.96
dtc_gross = float(dtc["gross"])
total = b2b_invoiced + dtc_gross
print(f"DTC as % of total revenue: {dtc_gross/total*100:.1f}%")

print(f"\n{'='*50}")
print(f"CURRENT DATASET vs INDUSTRY NORMS (mid-market CPG)")
print(f"{'='*50}")
print(f"")
print(f"{'Metric':<35} {'Ours':<15} {'Industry':<15}")
print(f"{'-'*65}")
print(f"{'Deduction % of gross':<35} {'7.0%':<15} {'10-20%':<15}")
print(f"{'% orders with deductions':<35} {r['orders_with_deductions']/r['total_orders']*100:.0f}%{'':9} {'30-50%':<15}")
print(f"{'Avg deduction size':<35} ${float(ded['total'])/ded['n']:.0f}{'':10} {'$300-$2,000':<15}")
print(f"{'DTC as % of total':<35} {dtc_gross/total*100:.1f}%{'':9} {'5-15%':<15}")
print(f"{'DTC AOV':<35} ${float(dtc['avg_order']):.0f}{'':12} {'$45-$80':<15}")
print(f"{'B2B avg order':<35} ${b2b_invoiced/r['total_orders']:,.0f}{'':5} {'$3,000-$8,000':<15}")
print(f"{'Deductions per order':<35} {ded['n']/r['total_orders']:.2f}{'':10} {'0.5-1.5':<15}")

conn.close()
