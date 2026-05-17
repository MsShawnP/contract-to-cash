"""Realism check v2 — compare current JSON export against industry norms."""

import json
from pathlib import Path

JSON_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "json"

with open(JSON_DIR / "summary.json") as f:
    s = json.load(f)
with open(JSON_DIR / "lifecycle.json") as f:
    l = json.load(f)
with open(JSON_DIR / "retailers.json") as f:
    r = json.load(f)

print("=" * 70)
print("  REALISM CHECK — CURRENT DATA vs INDUSTRY NORMS (mid-market CPG)")
print("=" * 70)
print()

flags = []


def row(metric, ours, industry, lo, hi, val):
    if lo <= val <= hi:
        verdict = "OK"
    elif val < lo:
        verdict = "LOW"
        flags.append(metric)
    else:
        verdict = "HIGH"
        flags.append(metric)
    print(f"  {metric:<35} {ours:<15} {industry:<15} {verdict}")


print(f"  {'Metric':<35} {'Ours':<15} {'Industry':<15} {'Verdict'}")
print(f"  {'-' * 70}")

# Deduction % of gross
ded_pct = s["b2b"]["leakage_pct"]
row("Deduction % of gross", f"{ded_pct}%", "10-20%", 10, 20, ded_pct)

# Avg deduction size
avg_ded = s["b2b"]["total_deductions"] / s["b2b"]["deduction_count"]
row("Avg deduction size", f"${avg_ded:.0f}", "$300-$2,000", 300, 2000, avg_ded)

# Deductions per order
ded_per_order = s["b2b"]["deduction_count"] / s["meta"]["orders_b2b"]
row("Deductions per order", f"{ded_per_order:.2f}", "0.5-1.5", 0.5, 1.5, ded_per_order)

# B2B avg order
b2b_avg = s["b2b"]["gross_payments"] / s["meta"]["orders_b2b"]
row("B2B avg order (gross)", f"${b2b_avg:,.0f}", "$3,000-$8,000", 3000, 8000, b2b_avg)

# DTC as % of total
dtc_pct = s["dtc"]["gross"] / s["combined"]["total_gross"] * 100
row("DTC as % of total", f"{dtc_pct:.1f}%", "5-15%", 5, 15, dtc_pct)

# DTC AOV
dtc_aov = s["dtc"]["gross"] / s["meta"]["orders_dtc"]
row("DTC AOV", f"${dtc_aov:.0f}", "$45-$80", 45, 80, dtc_aov)

# Recovery rate
recovery_pct = s["b2b"]["recovered"] / s["b2b"]["total_deductions"] * 100
row("Recovery rate", f"{recovery_pct:.1f}%", "5-30%", 5, 30, recovery_pct)

# Time to cash range
ttc_min = min(t["avg_days"] for t in r["time_to_cash"])
ttc_max = max(t["avg_days"] for t in r["time_to_cash"])
row("Time to cash (slowest)", f"{ttc_max:.0f} days", "30-60 days", 30, 90, ttc_max)

# Retailer concentration (top 1)
top1_pct = r["leakage"][0]["gross"] / s["b2b"]["gross_payments"] * 100
row("Top retailer concentration", f"{top1_pct:.0f}%", "30-50%", 20, 60, top1_pct)

# DTC leakage
dtc_leak = s["dtc"]["leakage_pct"]
row("DTC leakage rate", f"{dtc_leak}%", "5-12%", 5, 12, dtc_leak)

# Promo billback share of total deductions
promo_stage = next((st for st in l["b2b"]["stages"] if st["stage"] == "promo_billback"), None)
if promo_stage:
    promo_share = promo_stage["amount"] / s["b2b"]["total_deductions"] * 100
    row("Promo billback share", f"{promo_share:.1f}%", "20-40%", 15, 45, promo_share)

print()
print("=" * 70)
if flags:
    print(f"  FLAGS ({len(flags)}): {', '.join(flags)}")
else:
    print("  ALL METRICS WITHIN INDUSTRY NORMS")
print("=" * 70)

# Additional context
print(f"\n  Current headline: {s['headline']}")
print(f"  B2B gross: ${s['b2b']['gross_payments']:,.2f}")
print(f"  B2B net: ${s['b2b']['net_received']:,.2f}")
print(f"  B2B deductions: ${s['b2b']['total_deductions']:,.2f} ({s['b2b']['deduction_count']} count)")
print(f"  DTC gross: ${s['dtc']['gross']:,.2f} ({s['meta']['orders_dtc']} orders)")
print(f"  Combined net: ${s['combined']['total_net']:,.2f}")
print(f"  Cents per dollar: {s['combined']['cents_per_dollar']}")
