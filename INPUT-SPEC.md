# Contract to Cash — Client Data Input Specification

Contract to Cash quantifies **revenue leakage** — how many cents of every
invoiced dollar arrive as cash — overall and per retailer, plus average
time-to-cash. It needs one **invoice ledger**. It is a money tool, so every
figure prints its basis (gross invoiced vs net cash received) and window (the
invoice-date span). Not POS-shaped, so it uses the generic column contract.

Map your headers in `engagement.yml`; identifiers are read as text; a missing
required column yields a branded Data Readiness Report, not a result.

## §Invoices — the invoice-to-cash ledger (required)
One row per invoice.

| Column | Type | Required | Used for |
|---|---|---|---|
| `invoice_id` | identifier (text) | **required, unique** | the ledger key |
| `retailer` | string | **required** | per-retailer leakage + time-to-cash |
| `invoice_date` | date | **required** | window; time-to-cash start |
| `invoice_amount` | number ≥ 0 | **required** | gross invoiced dollars (the basis numerator) |
| `amount_received` | number ≥ 0 | **required** | net cash received against the invoice |
| `payment_date` | date | optional | cash-received date; **blank = unpaid** (excluded from time-to-cash) |
| `deduction_amount` | number ≥ 0 | optional | disclosed deductions (informational) |

Leakage = `invoice_amount − amount_received`; leakage % = leakage ÷ invoiced;
cents-per-dollar = received ÷ invoiced. Time-to-cash = `payment_date −
invoice_date` in days, averaged per retailer over paid invoices.

## Column mapping (`engagement.yml`)
```yaml
client: {name: Your Brand}
engagement: {id: YB-2026-08}
as_of_date: 2026-06-30
inputs:
  input: client-data/invoices.csv
columns:
  invoice_id: "Invoice #"
  retailer: "Customer"
  invoice_date: "Invoice Date"
  invoice_amount: "Billed"
  amount_received: "Paid"
  payment_date: "Paid Date"
```

Run: `python client_mode.py --config engagement.yml --input client-data/invoices.csv`
