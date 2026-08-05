"""Client-mode tests for Contract to Cash (checklist §6).

Skipped unless the shared ``lailara_engagement`` lib is installed. Fixtures are
generated on the fly — no client identifiers, no committed data.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("lailara_engagement")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client_mode  # noqa: E402

LEDGER = (
    "invoice_id,retailer,invoice_date,invoice_amount,amount_received,payment_date\n"
    "INV1,Walmart,2023-01-05,1000,900,2023-01-30\n"    # 25 days
    "INV2,Walmart,2023-02-05,1000,850,2023-03-01\n"    # 24 days
    "INV3,Costco,2023-01-10,500,500,2023-02-01\n"      # 22 days
    "INV4,Costco,2023-02-10,500,450,2023-03-05\n"      # 23 days
)


def _write(d: Path, text=LEDGER, name="invoices.csv"):
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


def _cfg(d: Path, columns=None):
    import yaml
    p = d / "engagement.demo.yml"
    p.write_text(yaml.safe_dump({
        "client": {"name": "Cinderhaven Provisions (demo)"}, "engagement": {"id": "T-1"},
        "as_of_date": "2026-01-02", "demo": True, "columns": columns or {}}), encoding="utf-8")
    return p


def test_clean_ledger_computes_leakage(tmp_path):
    inp = _write(tmp_path)
    cfg = _cfg(tmp_path)
    res = client_mode.run(str(cfg), str(inp), str(tmp_path / "out"))
    assert res["status"] == "ok"
    assert res["total_invoiced"] == 3000.00
    assert res["total_net"] == 2700.00
    assert res["total_leakage"] == 300.00
    assert res["leakage_pct"] == 10.0
    assert res["cents_per_dollar"] == 90.0
    assert Path(res["report"]).is_file() and Path(res["csv"]).is_file()


def test_per_retailer_leakage_and_time_to_cash(tmp_path):
    inp = _write(tmp_path)
    cfg = _cfg(tmp_path)
    res = client_mode.run(str(cfg), str(inp), str(tmp_path / "out"))
    import csv as _csv
    rows = {r["retailer"]: r for r in _csv.DictReader(open(res["csv"], encoding="utf-8"))}
    assert float(rows["Walmart"]["leakage_pct"]) == 12.5
    assert float(rows["Walmart"]["avg_days_to_cash"]) == 24.5     # (25+24)/2
    assert float(rows["Costco"]["leakage_pct"]) == 5.0
    assert float(rows["Costco"]["avg_days_to_cash"]) == 22.5      # (22+23)/2


def test_deliverable_prints_basis_window_draft(tmp_path):
    inp = _write(tmp_path)
    cfg = _cfg(tmp_path)
    res = client_mode.run(str(cfg), str(inp), str(tmp_path / "out"))
    html = Path(res["report"]).read_text(encoding="utf-8")
    assert "gross invoiced dollars vs net cash received" in html
    assert "Window: invoices" in html
    assert "90.0¢ of every invoiced dollar" in html
    assert "DRAFT" in html
    assert "Basis" in html   # provenance footer extra


def test_missing_amount_received_blocks(tmp_path):
    text = LEDGER.replace(",amount_received", ",x_received").replace(
        ",900,", ",").replace(",850,", ",").replace(",500,", ",").replace(",450,", ",")
    # simpler: drop the column entirely
    import pandas as pd
    inp = tmp_path / "invoices.csv"
    df = pd.read_csv(_write(tmp_path, name="tmp.csv")).drop(columns=["amount_received"])
    df.to_csv(inp, index=False)
    cfg = _cfg(tmp_path)
    res = client_mode.run(str(cfg), str(inp), str(tmp_path / "out"))
    assert res["status"] == "blocked"
    report = Path(res["readiness_report"]).read_text(encoding="utf-8")
    assert "amount_received" in report


def test_unpaid_invoice_excluded_from_time_to_cash(tmp_path):
    text = LEDGER + "INV5,Walmart,2023-03-05,1000,0,\n"   # unpaid: blank payment_date
    inp = _write(tmp_path, text=text)
    cfg = _cfg(tmp_path)
    res = client_mode.run(str(cfg), str(inp), str(tmp_path / "out"))
    assert res["status"] == "ok"
    import csv as _csv
    rows = {r["retailer"]: r for r in _csv.DictReader(open(res["csv"], encoding="utf-8"))}
    # Walmart time-to-cash unchanged (24.5) — the unpaid invoice is excluded.
    assert float(rows["Walmart"]["avg_days_to_cash"]) == 24.5


def test_header_mapping(tmp_path):
    text = (
        "Invoice #,Customer,Invoice Date,Billed,Paid,Paid Date\n"
        "INV1,Walmart,2023-01-05,1000,900,2023-01-30\n"
        "INV2,Costco,2023-01-10,500,500,2023-02-01\n"
    )
    inp = _write(tmp_path, text=text)
    cfg = _cfg(tmp_path, columns={"invoice_id": "Invoice #", "retailer": "Customer",
                                  "invoice_date": "Invoice Date", "invoice_amount": "Billed",
                                  "amount_received": "Paid", "payment_date": "Paid Date"})
    res = client_mode.run(str(cfg), str(inp), str(tmp_path / "out"))
    assert res["status"] == "ok"
    assert res["total_invoiced"] == 1500.00
    assert res["total_leakage"] == 100.00
