"""Comprehensive data audit for Contract-to-Cash JSON layer.

Checks internal consistency, cross-file reconciliation, logical ranges,
and structural integrity without requiring database access.
"""

import json
import sys
from pathlib import Path

JSON_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "json"

with open(JSON_DIR / "summary.json") as f:
    summary = json.load(f)
with open(JSON_DIR / "lifecycle.json") as f:
    lifecycle = json.load(f)
with open(JSON_DIR / "retailers.json") as f:
    retailers = json.load(f)

checks = []
failures = []


def check(name, expected, actual, tolerance=0.01):
    if expected == 0:
        passed = actual == 0
    else:
        passed = abs(actual - expected) / abs(expected) <= tolerance
    status = "PASS" if passed else "FAIL"
    checks.append((name, passed))
    if not passed:
        failures.append((name, expected, actual))
    print(f"  [{status}] {name}")
    if not passed:
        print(f"         Expected: {expected}")
        print(f"         Actual:   {actual}")


def check_bool(name, condition):
    status = "PASS" if condition else "FAIL"
    checks.append((name, condition))
    if not condition:
        failures.append((name, True, False))
    print(f"  [{status}] {name}")


print("=" * 60)
print("  CONTRACT-TO-CASH DATA AUDIT (JSON layer)")
print("=" * 60)

# --- Section 1: Summary internal consistency ---
print("\n--- Summary.json internal math ---\n")

check("combined.total_gross = b2b.gross_payments + dtc.gross",
      summary["b2b"]["gross_payments"] + summary["dtc"]["gross"],
      summary["combined"]["total_gross"])

check("combined.total_net = b2b.net_received + dtc.net_received",
      summary["b2b"]["net_received"] + summary["dtc"]["net_received"],
      summary["combined"]["total_net"])

check("combined.cents_per_dollar = total_net / total_gross * 100",
      round(summary["combined"]["total_net"] / summary["combined"]["total_gross"] * 100, 1),
      summary["combined"]["cents_per_dollar"])

b2b_leakage_computed = round(
    (summary["b2b"]["gross_payments"] - summary["b2b"]["net_received"])
    / summary["b2b"]["gross_payments"] * 100, 1
)
check("b2b.leakage_pct = (gross - net) / gross * 100",
      b2b_leakage_computed, summary["b2b"]["leakage_pct"])

dtc_leakage_computed = round(
    (summary["dtc"]["gross"] - summary["dtc"]["net_received"])
    / summary["dtc"]["gross"] * 100, 1
)
check("dtc.leakage_pct = (gross - net) / gross * 100",
      dtc_leakage_computed, summary["dtc"]["leakage_pct"])

check("b2b.total_deductions = gross_payments - net_received",
      round(summary["b2b"]["gross_payments"] - summary["b2b"]["net_received"], 2),
      summary["b2b"]["total_deductions"])

dtc_leakage_sum = (
    summary["dtc"]["processing_fees"]
    + summary["dtc"]["refunds"]
    + summary["dtc"]["chargebacks_lost"]
)
check("dtc leakage components sum = gross - net",
      round(summary["dtc"]["gross"] - summary["dtc"]["net_received"], 2),
      round(dtc_leakage_sum, 2))

# --- Section 2: Lifecycle matches summary ---
print("\n--- Lifecycle.json vs Summary.json ---\n")

check("lifecycle.b2b.gross = summary.b2b.gross_payments",
      summary["b2b"]["gross_payments"], lifecycle["b2b"]["gross"])

check("lifecycle.b2b.net = summary.b2b.net_received",
      summary["b2b"]["net_received"], lifecycle["b2b"]["net"])

check("lifecycle.dtc.gross = summary.dtc.gross",
      summary["dtc"]["gross"], lifecycle["dtc"]["gross"])

check("lifecycle.dtc.net = summary.dtc.net_received",
      summary["dtc"]["net_received"], lifecycle["dtc"]["net"])

b2b_stages_sum = sum(s["amount"] for s in lifecycle["b2b"]["stages"])
check("sum(b2b stages) = b2b total deductions",
      summary["b2b"]["total_deductions"], round(b2b_stages_sum, 2))

check("b2b gross - sum(stages) = net",
      lifecycle["b2b"]["net"],
      round(lifecycle["b2b"]["gross"] - b2b_stages_sum, 2))

dtc_stages_sum = sum(s["amount"] for s in lifecycle["dtc"]["stages"])
check("sum(dtc stages) = dtc total leakage",
      round(summary["dtc"]["gross"] - summary["dtc"]["net_received"], 2),
      round(dtc_stages_sum, 2))

lifecycle_ded_count = sum(s["count"] for s in lifecycle["b2b"]["stages"])
check("lifecycle b2b deduction count = summary.b2b.deduction_count",
      summary["b2b"]["deduction_count"], lifecycle_ded_count)

# --- Section 3: Retailers.json vs Summary.json ---
print("\n--- Retailers.json vs Summary.json ---\n")

check("retailer count in leakage = meta.retailers_b2b",
      summary["meta"]["retailers_b2b"], len(retailers["leakage"]))

retailer_gross_sum = sum(r["gross"] for r in retailers["leakage"])
check("sum(retailer gross) = summary.b2b.gross_payments",
      summary["b2b"]["gross_payments"], round(retailer_gross_sum, 2))

retailer_net_sum = sum(r["net"] for r in retailers["leakage"])
check("sum(retailer net) = summary.b2b.net_received",
      summary["b2b"]["net_received"], round(retailer_net_sum, 2))

# Per-retailer leakage_pct
print("\n--- Per-retailer leakage_pct verification ---\n")
for r in retailers["leakage"]:
    computed = round((r["gross"] - r["net"]) / r["gross"] * 100, 1)
    check(f"{r['name']} leakage_pct", computed, r["leakage_pct"])

# --- Section 4: Deduction mix aggregation ---
print("\n--- Deduction mix aggregation ---\n")

mix_total = sum(
    d["amount"]
    for retailer_deds in retailers["deduction_mix"].values()
    for d in retailer_deds
)
check("sum(deduction_mix amounts) = total deductions",
      summary["b2b"]["total_deductions"], round(mix_total, 2))

for stage in lifecycle["b2b"]["stages"]:
    stage_type = stage["stage"]
    mix_by_type = sum(
        d["amount"]
        for retailer_deds in retailers["deduction_mix"].values()
        for d in retailer_deds
        if d["type"] == stage_type
    )
    check(f"deduction_mix {stage_type} total matches lifecycle",
          stage["amount"], round(mix_by_type, 2))

# --- Section 5: Logical range checks ---
print("\n--- Range and sanity checks ---\n")

check_bool("cents_per_dollar between 0 and 100",
           0 < summary["combined"]["cents_per_dollar"] < 100)
check_bool("b2b leakage_pct between 0 and 100",
           0 < summary["b2b"]["leakage_pct"] < 100)
check_bool("dtc leakage_pct between 0 and 100",
           0 < summary["dtc"]["leakage_pct"] < 100)
check_bool("all retailer leakage_pcts positive",
           all(r["leakage_pct"] > 0 for r in retailers["leakage"]))
check_bool("all deduction amounts positive",
           all(s["amount"] > 0 for s in lifecycle["b2b"]["stages"]))
check_bool("b2b net < gross (deductions happened)",
           lifecycle["b2b"]["net"] < lifecycle["b2b"]["gross"])
check_bool("dtc net < gross (fees happened)",
           lifecycle["dtc"]["net"] < lifecycle["dtc"]["gross"])
check_bool("no negative recovery values",
           all(s.get("recovered", 0) >= 0 for s in lifecycle["b2b"]["stages"]))
check_bool("all time_to_cash avg_days > 0",
           all(t["avg_days"] > 0 for t in retailers["time_to_cash"]))
check_bool("all time_to_cash avg_days < 120 (realistic)",
           all(t["avg_days"] < 120 for t in retailers["time_to_cash"]))
check_bool("time_to_cash retailer count = leakage retailer count",
           len(retailers["leakage"]) == len(retailers["time_to_cash"]))

# --- Section 6: Recovery logic ---
print("\n--- Recovery logic ---\n")

check_bool("total recovered < total deductions",
           summary["b2b"]["recovered"] < summary["b2b"]["total_deductions"])

recovery_rate = summary["b2b"]["recovered"] / summary["b2b"]["total_deductions"] * 100
check_bool(f"recovery rate ({recovery_rate:.1f}%) is plausible (0-50%)",
           0 < recovery_rate < 50)

lifecycle_recovered = sum(s.get("recovered", 0) for s in lifecycle["b2b"]["stages"])
check("sum(stage recovered) = summary.b2b.recovered",
      summary["b2b"]["recovered"], round(lifecycle_recovered, 2))

# --- Section 7: Structural completeness ---
print("\n--- Structural completeness ---\n")

check_bool("all 9 deduction types present in lifecycle",
           len(lifecycle["b2b"]["stages"]) == 9)

all_retailers_in_mix = set(retailers["deduction_mix"].keys())
all_retailers_in_leakage = {r["name"] for r in retailers["leakage"]}
check_bool("deduction_mix covers all leakage retailers",
           all_retailers_in_leakage == all_retailers_in_mix)

all_retailers_in_ttc = {t["name"] for t in retailers["time_to_cash"]}
check_bool("time_to_cash covers all leakage retailers",
           all_retailers_in_leakage == all_retailers_in_ttc)

check_bool("headline_ratio matches leakage_cents",
           abs(summary["headline_ratio"] * 100 - summary["combined"]["leakage_cents"]) < 0.5)

check_bool("meta.time_window is non-empty",
           len(summary["meta"]["time_window"]) > 0)

check_bool("meta.skus > 0", summary["meta"]["skus"] > 0)

# --- Section 8: Ordering and sorting ---
print("\n--- Data ordering ---\n")

leakage_amounts = [r["gross"] - r["net"] for r in retailers["leakage"]]
check_bool("retailers sorted by leakage amount descending",
           leakage_amounts == sorted(leakage_amounts, reverse=True))

ttc_days = [t["avg_days"] for t in retailers["time_to_cash"]]
check_bool("time_to_cash sorted by avg_days descending",
           ttc_days == sorted(ttc_days, reverse=True))

for stage in lifecycle["b2b"]["stages"]:
    stages_sorted = lifecycle["b2b"]["stages"]
    stage_amounts = [s["amount"] for s in stages_sorted]
    check_bool("b2b stages sorted by amount descending",
               stage_amounts == sorted(stage_amounts, reverse=True))
    break  # only need to check once

# --- Results ---
print("\n" + "=" * 60)
total = len(checks)
passed = sum(1 for _, p in checks if p)
failed = total - passed
if failed == 0:
    print(f"  ALL {total} CHECKS PASSED")
else:
    print(f"  {failed} of {total} CHECKS FAILED:")
    for name, exp, act in failures:
        print(f"    - {name}: expected {exp}, got {act}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
