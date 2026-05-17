"""Backfill raw.shopify_transactions (and refunds/chargebacks) to match
fct_orders DTC volume for CY2025.

Existing: 6,800 CY2025 transactions, $288K gross, $42.46 AOV
Target:  26,333 CY2025 transactions (matching fct_orders), ~$55 blended AOV
Insert:  19,533 new transactions + proportional refunds/chargebacks
"""

import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

import psycopg2
import psycopg2.extras

random.seed(42)

conn = psycopg2.connect(
    "postgresql://postgres:REDACTED@localhost:5432/cinderhaven",
    cursor_factory=psycopg2.extras.RealDictCursor,
)
cur = conn.cursor()

# --- Config ---
TARGET_CY2025 = 26333
EXISTING_CY2025 = 6800
TO_INSERT = TARGET_CY2025 - EXISTING_CY2025  # 19,533

# Existing max ID is SH-011000 / TXN-SH-011000
START_ID = 11001

# Target blended AOV ~$55; existing contributes $288K at $42.46
# New records need: (26333 * 55) - 288712 = ~$1,159,603 → avg $59.37
NEW_AOV_MEAN = 59.37
NEW_AOV_STD = 22.0  # wide spread for realism
AOV_MIN = 12.0
AOV_MAX = 180.0

# Monthly weights (follow existing seasonal pattern, scaled)
MONTHLY_WEIGHTS = {
    1: 397, 2: 425, 3: 482, 4: 510, 5: 538, 6: 567,
    7: 538, 8: 510, 9: 567, 10: 623, 11: 793, 12: 850,
}
TOTAL_WEIGHT = sum(MONTHLY_WEIGHTS.values())

# Payment method distribution
PAYMENT_METHODS = ["credit_card", "debit_card", "shop_pay", "apple_pay"]
PAYMENT_WEIGHTS = [0.499, 0.203, 0.200, 0.098]

# Processing fee: ~3.6% of order amount (existing: $10,413 / $288,712 = 3.61%)
FEE_RATE_MEAN = 0.036
FEE_RATE_STD = 0.005

# Refund rate: 4.01% of transactions, scale proportionally
EXISTING_REFUNDS = 273
REFUND_RATE = EXISTING_REFUNDS / EXISTING_CY2025
NEW_REFUNDS = round(TO_INSERT * REFUND_RATE)  # ~783

# Chargeback rate: 0.78% of transactions
EXISTING_CHARGEBACKS = 53
CB_RATE = EXISTING_CHARGEBACKS / EXISTING_CY2025
NEW_CHARGEBACKS = round(TO_INSERT * CB_RATE)  # ~152
CB_LOST_RATE = 0.60  # ~60% lost (current: $1498/$2488 ≈ 60%)

CB_REASONS = [
    "product_not_received", "fraudulent", "duplicate",
    "subscription_canceled", "credit_not_processed",
]


def random_date_in_month(year, month):
    """Random date within a given month."""
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    start = date(year, month, 1)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def quantize(val):
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# --- Distribute inserts across months ---
monthly_counts = {}
remaining = TO_INSERT
for mo in range(1, 13):
    if mo == 12:
        monthly_counts[mo] = remaining
    else:
        count = round(TO_INSERT * MONTHLY_WEIGHTS[mo] / TOTAL_WEIGHT)
        monthly_counts[mo] = count
        remaining -= count

print(f"Inserting {TO_INSERT} transactions across CY2025:")
for mo, ct in monthly_counts.items():
    print(f"  Month {mo:2d}: {ct}")

# --- Generate transactions ---
transactions = []
current_id = START_ID

for mo in range(1, 13):
    for _ in range(monthly_counts[mo]):
        order_amount = max(AOV_MIN, min(AOV_MAX, random.gauss(NEW_AOV_MEAN, NEW_AOV_STD)))
        fee_rate = max(0.015, min(0.06, random.gauss(FEE_RATE_MEAN, FEE_RATE_STD)))
        processing_fee = order_amount * fee_rate
        net_amount = order_amount - processing_fee

        txn_date = random_date_in_month(2025, mo)
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]

        transactions.append((
            f"TXN-SH-{current_id:06d}",
            f"SH-{current_id:06d}",
            txn_date,
            quantize(order_amount),
            quantize(processing_fee),
            quantize(net_amount),
            payment_method,
            "completed",
        ))
        current_id += 1

print(f"\nGenerated {len(transactions)} transactions")
total_gross = sum(float(t[3]) for t in transactions)
print(f"New gross: ${total_gross:,.2f}")
print(f"New AOV: ${total_gross / len(transactions):.2f}")
blended_gross = total_gross + 288712.44
print(f"Blended gross: ${blended_gross:,.2f}")
print(f"Blended AOV: ${blended_gross / TARGET_CY2025:.2f}")

# --- Generate refunds ---
# Pick random transactions to refund (partial or full)
refund_indices = random.sample(range(len(transactions)), NEW_REFUNDS)
cur.execute("SELECT MAX(CAST(SUBSTRING(refund_id FROM 5) AS int)) FROM raw.shopify_refunds")
max_refund_id = cur.fetchone()["max"] or 0
refund_id_start = max_refund_id + 1

REFUND_REASONS = [
    "customer_request", "defective_product", "product_damaged",
    "late_delivery", "wrong_item",
]

refunds = []
for i, idx in enumerate(refund_indices):
    txn = transactions[idx]
    order_amount = float(txn[3])
    # 40% full refund, 60% partial (50-90% of order)
    if random.random() < 0.4:
        refund_amount = order_amount
        refund_type = "full"
    else:
        refund_amount = order_amount * random.uniform(0.5, 0.9)
        refund_type = "partial"

    # Refund happens 3-30 days after transaction
    refund_date = txn[2] + timedelta(days=random.randint(3, 30))
    if refund_date > date(2025, 12, 31):
        refund_date = date(2025, 12, 31)

    refunds.append((
        f"REF-{refund_id_start + i:06d}",
        txn[1],  # order_id
        refund_date,
        quantize(refund_amount),
        refund_type,
        random.choice(REFUND_REASONS),
    ))

print(f"\nGenerated {len(refunds)} refunds")
total_refunds = sum(float(r[3]) for r in refunds)
print(f"New refund total: ${total_refunds:,.2f}")

# --- Generate chargebacks ---
cb_indices = random.sample(
    [i for i in range(len(transactions)) if i not in refund_indices],
    NEW_CHARGEBACKS,
)
cur.execute("SELECT MAX(CAST(SUBSTRING(chargeback_id FROM 4) AS int)) FROM raw.shopify_chargebacks")
max_cb_id = cur.fetchone()["max"] or 0
cb_id_start = max_cb_id + 1

chargebacks = []
for i, idx in enumerate(cb_indices):
    txn = transactions[idx]
    order_amount = float(txn[3])
    cb_amount = order_amount  # chargebacks are typically full amount
    cb_fee = 15.0  # standard chargeback fee

    cb_date = txn[2] + timedelta(days=random.randint(15, 60))
    if cb_date > date(2025, 12, 31):
        cb_date = date(2025, 12, 31)

    outcome = "lost" if random.random() < CB_LOST_RATE else "won"
    reason = random.choice(CB_REASONS)

    chargebacks.append((
        f"CB-{cb_id_start + i:06d}",
        txn[1],  # order_id
        cb_date,
        quantize(cb_amount),
        quantize(cb_fee),
        reason,
        outcome,
    ))

print(f"Generated {len(chargebacks)} chargebacks")
cb_lost = [c for c in chargebacks if c[6] == "lost"]
print(f"  Lost: {len(cb_lost)}, total ${sum(float(c[3]) for c in cb_lost):,.2f}")

# --- Insert into database ---
print("\n--- Inserting into database ---")

cur.execute("BEGIN")

# Transactions
psycopg2.extras.execute_values(
    cur,
    """INSERT INTO raw.shopify_transactions
       (transaction_id, order_id, transaction_date, order_amount,
        processing_fee, net_amount, payment_method, status)
       VALUES %s""",
    transactions,
    page_size=1000,
)
print(f"  Inserted {len(transactions)} transactions")

# Refunds
psycopg2.extras.execute_values(
    cur,
    """INSERT INTO raw.shopify_refunds
       (refund_id, order_id, refund_date, refund_amount, refund_type, reason)
       VALUES %s""",
    refunds,
    page_size=1000,
)
print(f"  Inserted {len(refunds)} refunds")

# Chargebacks
psycopg2.extras.execute_values(
    cur,
    """INSERT INTO raw.shopify_chargebacks
       (chargeback_id, order_id, chargeback_date, chargeback_amount,
        chargeback_fee, reason, outcome)
       VALUES %s""",
    chargebacks,
    page_size=1000,
)
print(f"  Inserted {len(chargebacks)} chargebacks")

conn.commit()
print("\n  COMMITTED.")

# --- Verify ---
cur.execute("""SELECT COUNT(*) as n, SUM(order_amount) as gross
               FROM raw.shopify_transactions
               WHERE transaction_date BETWEEN '2025-01-01' AND '2025-12-31'""")
r = cur.fetchone()
print(f"\nVerification - CY2025 transactions: {r['n']}, gross ${float(r['gross']):,.2f}")
print(f"  AOV: ${float(r['gross']) / r['n']:.2f}")

cur.execute("""SELECT COUNT(*) as n, SUM(refund_amount) as total
               FROM raw.shopify_refunds
               WHERE refund_date BETWEEN '2025-01-01' AND '2025-12-31'""")
r = cur.fetchone()
print(f"  Refunds: {r['n']}, total ${float(r['total']):,.2f}")

cur.execute("""SELECT COUNT(*) as n, SUM(chargeback_amount) as total
               FROM raw.shopify_chargebacks
               WHERE chargeback_date BETWEEN '2025-01-01' AND '2025-12-31'
                 AND outcome = 'lost'""")
r = cur.fetchone()
print(f"  Chargebacks lost: {r['n']}, total ${float(r['total']):,.2f}")

conn.close()
print("\nDone. Run export_json.py to regenerate the JSON.")
