"""Client-mode CLI for Contract to Cash.

Traces a client's own invoice-to-cash records to quantify revenue leakage — how
many cents of every invoiced dollar actually arrive as cash — overall and per
retailer, plus average time-to-cash. Runs locally via the shared
``lailara_engagement`` scaffold (tolerant intake + preflight + provenance).

This is a money tool: every headline figure prints its **basis** (gross invoiced
dollars vs net cash received) and **window** (the invoice-date span). It is not
POS-shaped (no store/sku/week), so it uses the generic column specs, not the POS
layer.

Required input: an **invoice ledger** — one row per invoice with the amount
invoiced and the cash received (plus optional payment date for time-to-cash and
a deduction amount). A missing required column blocks with a branded Data
Readiness Report; a clean run writes a draft-watermarked, provenance-footed
**Revenue Leakage Summary** (HTML) + a per-retailer CSV to ``client-output/``.

Usage:
    python client_mode.py --config engagement.yml --input client-data/invoices.csv \
        [--out client-output] [--final]
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd

from lailara_engagement import (
    ColumnSpec,
    PreflightSpec,
    build_provenance,
    load_config,
    read_table,
    run_preflight,
    validation_status_label,
    write_report,
)
from lailara_engagement import palette as P
from lailara_engagement.pos import to_frame
from lailara_engagement.provenance import Provenance

TOOL = "contract-to-cash"
TOOL_VERSION = "1.0"
BASIS_LABEL = "gross invoiced dollars vs net cash received"


def _ledger_spec() -> PreflightSpec:
    return PreflightSpec(tool=TOOL, version=TOOL_VERSION, columns=[
        ColumnSpec(name="invoice_id", dtype="identifier", required=True, unique=True,
                   description="unique invoice id", spec_ref="INPUT-SPEC §Invoices"),
        ColumnSpec(name="retailer", dtype="string", required=True,
                   description="retailer / channel", spec_ref="INPUT-SPEC §Invoices"),
        ColumnSpec(name="invoice_date", dtype="date", required=True,
                   description="invoice date; drives the window + time-to-cash", spec_ref="INPUT-SPEC §Invoices"),
        ColumnSpec(name="invoice_amount", dtype="number", required=True, not_negative=True,
                   description="gross invoiced dollars", spec_ref="INPUT-SPEC §Invoices"),
        ColumnSpec(name="amount_received", dtype="number", required=True, not_negative=True,
                   description="net cash received against the invoice", spec_ref="INPUT-SPEC §Invoices"),
        ColumnSpec(name="payment_date", dtype="date", required=False, allow_blank=True,
                   description="cash-received date; blank = unpaid (excluded from time-to-cash)",
                   spec_ref="INPUT-SPEC §Invoices"),
        ColumnSpec(name="deduction_amount", dtype="number", required=False, allow_blank=True,
                   not_negative=True, description="disclosed deductions (informational)",
                   spec_ref="INPUT-SPEC §Invoices"),
    ])


def compute_leakage(frame: pd.DataFrame):
    invoiced = float(frame["invoice_amount"].sum())
    received = float(frame["amount_received"].sum())
    leakage = invoiced - received
    have_pay = "payment_date" in frame.columns

    rows = []
    for retailer, g in frame.groupby(frame["retailer"].fillna("(unspecified)")):
        inv = float(g["invoice_amount"].sum())
        net = float(g["amount_received"].sum())
        ttc = None
        if have_pay:
            paid = g[g["payment_date"].notna()]
            if not paid.empty:
                days = (paid["payment_date"] - paid["invoice_date"]).dt.days
                ttc = round(float(days[days >= 0].mean()), 1) if (days >= 0).any() else None
        rows.append({
            "retailer": str(retailer), "invoiced": round(inv, 2), "net_received": round(net, 2),
            "leakage": round(inv - net, 2),
            "leakage_pct": round((inv - net) / inv * 100, 1) if inv else 0.0,
            "avg_days_to_cash": ttc,
        })
    rows.sort(key=lambda r: r["leakage"], reverse=True)
    summary = {
        "total_invoiced": round(invoiced, 2), "total_net": round(received, 2),
        "total_leakage": round(leakage, 2),
        "leakage_pct": round(leakage / invoiced * 100, 1) if invoiced else 0.0,
        "cents_per_dollar": round(received / invoiced * 100, 1) if invoiced else 0.0,
        "n_invoices": len(frame),
    }
    return summary, rows


def _fmt_dollars(v):
    return "—" if v is None else f"${v:,.0f}"


def _deliverable_html(config, summary, retailers, window_label, limitations,
                      provenance: Provenance, *, draft: bool) -> str:
    esc = html.escape
    draft_class = " ll-draft" if draft else ""
    rows = "".join(
        f"<tr><td>{esc(r['retailer'])}</td><td class=num>{_fmt_dollars(r['invoiced'])}</td>"
        f"<td class=num>{_fmt_dollars(r['net_received'])}</td>"
        f"<td class=num>{r['leakage_pct']:.1f}%</td>"
        f"<td class=num>{'—' if r['avg_days_to_cash'] is None else f'{r['avg_days_to_cash']:.1f}'}</td></tr>"
        for r in retailers
    )
    lim = "".join(f"<li>{esc(x)}</li>" for x in limitations)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Revenue Leakage Summary — {esc(config.client_name)}</title><style>{_css(draft)}</style></head>
<body class="{draft_class.strip()}"><main class=ll-page>
<header class=ll-header>
  <div class=ll-eyebrow>Lailara LLC · Contract to Cash</div>
  <h1 class=ll-title>Revenue Leakage Summary</h1>
  <div class=ll-client>
    <div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
    <div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
    <div><span class=ll-k>As of</span> {esc(config.as_of_date.isoformat())}</div>
    <div><span class=ll-k>Prepared by</span> {esc(config.prepared_by)}</div>
  </div>
</header>
<section class=ll-banner>
  <div class=ll-score>{summary['cents_per_dollar']:.1f}¢ of every invoiced dollar arrives as cash</div>
  <div>{_fmt_dollars(summary['total_invoiced'])} invoiced · {_fmt_dollars(summary['total_net'])} net
       · {_fmt_dollars(summary['total_leakage'])} leaked ({summary['leakage_pct']:.1f}%) across {summary['n_invoices']:,} invoices</div>
  <div class=ll-basis>Basis: {esc(BASIS_LABEL)} · Window: {esc(window_label)}</div>
</section>
<section class=ll-section>
  <h2 class=ll-h2>By retailer</h2>
  <table class=ll-table><thead><tr><th>Retailer</th><th>Invoiced</th><th>Net received</th>
  <th>Leakage %</th><th>Avg days to cash</th></tr></thead><tbody>{rows}</tbody></table>
</section>
<section class=ll-section>
  <h2 class=ll-h2>Data limitations</h2>
  <ul class=ll-limitations>{lim}</ul>
</section>
{provenance.to_html()}
</main></body></html>"""


def _css(draft: bool) -> str:
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}
*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:34px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-banner{{border-radius:2px;padding:16px 20px;margin-bottom:32px;background:{P.LL_SG_SURFACE};color:{P.LL_SG_DARK}}}
.ll-score{{font-family:var(--s);font-weight:700;font-size:22px}}
.ll-basis{{font-size:12px;color:{P.LL_TEXT_SEC};margin-top:8px}}
.ll-section{{margin:0 0 32px}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;
margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table th{{text-align:left;background:{P.LL_CHICAGO};color:#fff;padding:8px 12px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-limitations{{margin:0;padding-left:20px}}.ll-limitations li{{margin-bottom:6px}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};
padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}
.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
"""


def run(config_path: str, input_path: str, out_dir: str, *, final: bool = False) -> dict:
    config = load_config(config_path)
    read = read_table(input_path)
    spec = _ledger_spec()
    report = run_preflight(read, spec, config)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=[read], config=config,
        validation_status=validation_status_label(report.status, report.n_warnings),
        extra={"Basis": BASIS_LABEL})
    if not report.passed:
        paths = write_report(report, config, str(out), provenance=provenance, draft=not final,
                             basename="data-readiness-report", title="Contract-to-Cash Data Readiness Report")
        return {"status": "blocked", "readiness_report": paths["html"]}

    frame = to_frame(read, report, spec)
    summary, retailers = compute_leakage(frame)
    first, last = frame["invoice_date"].min(), frame["invoice_date"].max()
    window_label = f"invoices {first.strftime('%b %d, %Y')} – {last.strftime('%b %d, %Y')}"

    limitations = [f.message for f in report.findings if f.severity == "warning"]
    if "payment_date" not in frame.columns:
        limitations.append("No payment_date column — time-to-cash omitted.")
    if not limitations:
        limitations.append("No warnings — the invoice ledger passed preflight cleanly.")

    import csv as _csv
    csv_path = out / "leakage-by-retailer.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(retailers[0].keys()) if retailers else ["retailer"])
        w.writeheader(); w.writerows(retailers)
    html_path = out / "revenue-leakage-summary.html"
    html_path.write_text(_deliverable_html(config, summary, retailers, window_label,
                                            limitations, provenance, draft=not final), encoding="utf-8")
    return {"status": "ok", **summary, "report": str(html_path), "csv": str(csv_path),
            "n_warnings": report.n_warnings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="contract-to-cash client mode")
    ap.add_argument("--config", required=True); ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="client-output"); ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.input, args.out, final=args.final)
    if result["status"] == "blocked":
        print(f"BLOCKED — data not ready. See {result['readiness_report']}")
        return 3
    print(f"{result['cents_per_dollar']:.1f}¢/$ arrives as cash · {_fmt_dollars(result['total_leakage'])} "
          f"leaked ({result['leakage_pct']:.1f}%) across {result['n_invoices']:,} invoices")
    print(f"report -> {result['report']}\ncsv    -> {result['csv']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
