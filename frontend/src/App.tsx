import { useEffect, useState } from "react";
import { loadData, type AppData } from "./data";
import "./styles.css";

export function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error">Failed to load data: {error}</div>;
  if (!data) return <div className="loading">Loading...</div>;

  const { summary } = data;

  return (
    <main className="page">
      <header className="hero">
        <div className="brand">
          <span className="brand-name">Cinderhaven Foods</span>
          <span className="brand-sub">Revenue Lifecycle Analysis</span>
        </div>
        <h1 className="headline">{summary.headline}</h1>
        <p className="subhead">
          Of ${(summary.combined.total_invoiced / 1e6).toFixed(1)}M invoiced
          across {summary.meta.retailers_total} channels over{" "}
          {summary.meta.time_window}, only $
          {(summary.combined.total_net / 1e6).toFixed(1)}M arrived as cash.
          The rest evaporated in deductions, fees, refunds, and timing.
        </p>
      </header>

      <section className="section" id="waterfall">
        <h2 className="section-title">Where the Money Goes</h2>
        <p className="section-body">
          Placeholder for waterfall chart — U7 implementation.
        </p>
      </section>

      <section className="section" id="retailers">
        <h2 className="section-title">Not All Retailers Leak Equally</h2>
        <p className="section-body">
          Placeholder for retailer comparison — U7 implementation.
        </p>
      </section>

      <section className="section" id="timing">
        <h2 className="section-title">Time Is Money (Literally)</h2>
        <p className="section-body">
          Placeholder for time-to-cash — U7 implementation.
        </p>
      </section>

      <footer className="footer">
        <p>
          Source: Cinderhaven Data Platform. {summary.meta.time_window}.{" "}
          {summary.b2b.deduction_count.toLocaleString()} deductions across{" "}
          {summary.meta.orders_b2b.toLocaleString()} B2B orders and{" "}
          {summary.meta.orders_dtc.toLocaleString()} DTC orders.
        </p>
      </footer>
    </main>
  );
}
