import { useEffect, useState } from "react";
import { loadData, type AppData } from "./data";
import { WaterfallChart } from "./components/WaterfallChart";
import { RetailerChart } from "./components/RetailerChart";
import { TimeToCashChart } from "./components/TimeToCashChart";
import "./styles.css";

function formatM(n: number): string {
  return `$${(n / 1e6).toFixed(1)}M`;
}

export function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error">Failed to load data: {error}</div>;
  if (!data) return <div className="loading">Loading...</div>;

  const { summary, lifecycle, retailers } = data;

  return (
    <main className="page">
      <header className="hero">
        <div className="brand">
          <span className="brand-name">Cinderhaven Foods</span>
          <span className="brand-sub">Revenue Lifecycle Analysis &middot; {summary.meta.time_window}</span>
        </div>
        <h1 className="headline">{summary.headline}</h1>
        <p className="subhead">
          Of {formatM(summary.combined.total_gross)} collected across{" "}
          {summary.meta.retailers_total} channels over {summary.meta.time_window},
          only {formatM(summary.combined.total_net)} arrived as net cash. The rest
          was absorbed by retailer deductions, processing fees, refunds, and
          chargebacks.
        </p>
        <div className="stat-row">
          <div className="stat-card">
            <span className="stat-value">
              {summary.combined.cents_per_dollar}&cent;
            </span>
            <span className="stat-label">per dollar invoiced</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{summary.b2b.leakage_pct}%</span>
            <span className="stat-label">B2B leakage rate</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{summary.dtc.leakage_pct}%</span>
            <span className="stat-label">DTC leakage rate</span>
          </div>
        </div>
      </header>

      <section className="section" id="waterfall">
        <h2 className="section-title">Where the Money Goes</h2>
        <p className="section-body">
          Of {formatM(lifecycle.b2b.gross)} in gross B2B payments acknowledged by
          retailers, {formatM(lifecycle.b2b.gross - lifecycle.b2b.net)} was deducted
          before cash arrived. Nine categories of deductions — from vague
          post-audit claims to short-ship penalties — each take their cut.
        </p>
        <div className="chart-container">
          <WaterfallChart lifecycle={lifecycle} />
        </div>
        <p className="footnote">
          Source: fct_payments, fct_deductions. Gross = sum of remittance
          gross_amount across {summary.b2b.remittance_count} remittances.
          Net = gross minus linked deductions. {summary.meta.time_window}.
        </p>
      </section>

      <section className="section" id="retailers">
        <h2 className="section-title">Not All Retailers Leak Equally</h2>
        <p className="section-body">
          Leakage rates range from{" "}
          {Math.min(...retailers.leakage.map((r) => r.leakage_pct))}% to{" "}
          {Math.max(...retailers.leakage.map((r) => r.leakage_pct))}% — a{" "}
          {(Math.max(...retailers.leakage.map((r) => r.leakage_pct)) - Math.min(...retailers.leakage.map((r) => r.leakage_pct))).toFixed(1)}{" "}
          percentage-point spread across eight direct retail partners. The
          smallest retailers by dollar flow show the highest deduction rates,
          while the largest are not necessarily the most aggressive.
        </p>
        <div className="chart-container">
          <RetailerChart retailers={retailers.leakage} />
        </div>
        <p className="footnote">
          Source: fct_payments grouped by retailer_name. Leakage % = (gross -
          net) / gross. {summary.meta.time_window}.
        </p>
      </section>

      <section className="section" id="timing">
        <h2 className="section-title">Time Is Money (Literally)</h2>
        <p className="section-body">
          Beyond what is deducted, the speed of payment varies dramatically.
          The fastest retailer (Whole Foods) averages 46 days to cash while
          the slowest (Costco) takes 56. That ten-day spread is working
          capital locked in transit — invisible on the P&L but real in cash
          flow.
        </p>
        <div className="chart-container">
          <TimeToCashChart timeToCash={retailers.time_to_cash} />
        </div>
        <p className="footnote">
          Source: fct_orders.order_date to fct_payments.received_date, joined
          via fct_deductions. Average days to cash across all linked
          order-payment pairs. {summary.meta.time_window}.
        </p>
      </section>

      <footer className="footer">
        <p>
          Source: Cinderhaven Data Platform. {summary.meta.time_window}.{" "}
          {summary.b2b.deduction_count.toLocaleString()} deductions across{" "}
          {summary.meta.orders_b2b.toLocaleString()} B2B orders and{" "}
          {summary.meta.orders_dtc.toLocaleString()} DTC orders. All figures
          reconcile with published project data.
        </p>
      </footer>
    </main>
  );
}
