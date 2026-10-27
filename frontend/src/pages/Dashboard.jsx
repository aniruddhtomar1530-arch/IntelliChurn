import { useRef, useState } from "react";
import { RefreshCw, Upload } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { errorMessage, importCustomers } from "../services/api.js";

function Metric({ label, value, note, change, icon, tone }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${tone}`}>{icon}</div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-footer">
        <span className="metric-change">{change}</span>
        <span>{note}</span>
      </div>
    </article>
  );
}

export default function Dashboard({ dashboard, customers, loading, error, reload, onSelectCustomer, onViewAll }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMessage("");
    setUploadError("");
    try {
      const result = await importCustomers(file);
      setUploadMessage(`Imported ${result.imported.toLocaleString()} customers.`);
      await reload();
    } catch (reason) {
      setUploadError(errorMessage(reason));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  const rate = dashboard?.labeled_churn_rate;
  const chartData = [...(dashboard?.recent_predictions || [])].reverse().map((prediction) => ({
    month: new Date(prediction.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    risk: Number((prediction.churn_probability * 100).toFixed(1)),
  }));
  const today = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  return (
    <main className="main-content">
      <header className="page-header">
        <div>
          <div className="eyebrow">{today.toUpperCase()}</div>
          <h1>Good morning, team <span className="wave">✳</span></h1>
          <p>Here’s what’s happening across your customer base.</p>
        </div>
        <div className="header-actions">
          <button className="button button-quiet" onClick={reload} disabled={loading}><RefreshCw size={16} className={loading ? "spin" : ""} /> Refresh</button>
          <input ref={inputRef} type="file" accept=".csv,text/csv" hidden onChange={handleUpload} />
          <button className="button button-primary" onClick={() => inputRef.current?.click()} disabled={uploading}><Upload size={16} /> {uploading ? "Importing…" : "Import data"}</button>
        </div>
      </header>

      {error && <div className="notice notice-error">{error}</div>}
      {uploadMessage && <div className="notice notice-success">{uploadMessage}</div>}
      {uploadError && <div className="notice notice-error">{uploadError}</div>}

      {!customers.length && !loading && (
        <div className="notice notice-info">
          <strong>Get started:</strong> Import a Telco churn CSV to load customer records. Train a model with
          <code> python backend/ml_pipeline/train_model.py</code> to enable churn predictions.
        </div>
      )}

      <section className="metrics-grid">
        <Metric label="Total customers" value={dashboard?.total_customers?.toLocaleString() ?? "—"} note="in your workspace" change="Live" tone="violet" icon={<span>♙</span>} />
        <Metric label="High risk" value={dashboard?.high_risk_customers?.toLocaleString() ?? "—"} note="latest predictions" change={dashboard?.high_risk_customers ? "Needs attention" : "No alerts"} tone="orange" icon={<span>⌁</span>} />
        <Metric label="Predictions made" value={dashboard?.predictions_made?.toLocaleString() ?? "—"} note="all-time" change="Model powered" tone="blue" icon={<span>◉</span>} />
        <Metric label="Observed churn" value={rate == null ? "—" : `${(rate * 100).toFixed(1)}%`} note="on labeled records" change={rate == null ? "No labels yet" : "Historical"} tone="green" icon={<span>↗</span>} />
      </section>

      <section className="content-grid">
        <article className="panel chart-panel">
          <div className="panel-heading">
            <div><h2>Recent prediction risk</h2><p>Latest customer churn probabilities</p></div>
              <span className="panel-tag"><span className="legend-dot" /> Churn probability</span>
          </div>
          <div className="chart-wrap">
              {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 12, right: 12, left: -16, bottom: 0 }}>
                  <defs><linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7357f2" stopOpacity={0.2} /><stop offset="95%" stopColor="#7357f2" stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid vertical={false} stroke="#edf0f5" />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#9299a8", fontSize: 12 }} dy={12} />
                  <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} axisLine={false} tickLine={false} tick={{ fill: "#9299a8", fontSize: 12 }} />
                  <Tooltip formatter={(value) => [`${value}%`, "Churn risk"]} contentStyle={{ borderRadius: 10, borderColor: "#edf0f5", boxShadow: "0 8px 24px #1a244015" }} />
                  <Area type="monotone" dataKey="risk" stroke="#7357f2" strokeWidth={2.5} fill="url(#riskFill)" />
                </AreaChart>
              </ResponsiveContainer>
              ) : <div className="empty-state">Prediction history will appear here after you assess customers.</div>}
          </div>
        </article>
        <article className="panel insight-panel">
          <div className="panel-heading"><div><h2>Retention pulse</h2><p>Portfolio health snapshot</p></div><span className="pulse-symbol">✦</span></div>
          <div className="pulse-score">{rate == null ? "—" : `${((1 - rate) * 100).toFixed(0)}%`}<span>retained</span></div>
          <div className="pulse-track"><span style={{ width: rate == null ? "0%" : `${(1 - rate) * 100}%` }} /></div>
          <p className="pulse-copy">{rate == null ? "Import labeled customer data to see your observed retention rate." : "Based on customers with known churn outcomes in your imported data."}</p>
          <div className="insight-divider" />
          <div className="insight-stat"><span>Predictions saved</span><strong>{dashboard?.predictions_made ?? 0}</strong></div>
          <div className="insight-stat"><span>High-risk customers</span><strong className="text-orange">{dashboard?.high_risk_customers ?? 0}</strong></div>
        </article>
      </section>

      <section className="panel table-panel">
        <div className="panel-heading table-heading">
          <div><h2>Customer directory</h2><p>{customers.length} customer{customers.length === 1 ? "" : "s"} loaded · select a customer to assess risk</p></div>
          <button className="text-button" onClick={onViewAll}>View all <span>→</span></button>
        </div>
        {loading && !customers.length ? <div className="empty-state">Loading customer data…</div> : customers.length ? (
          <div className="table-scroll"><table>
            <thead><tr><th>Customer</th><th>Contract</th><th>Tenure</th><th>Monthly charges</th><th>Churn label</th><th></th></tr></thead>
            <tbody>{customers.slice(0, 6).map((customer) => (
              <tr key={customer.customer_id} onClick={() => onSelectCustomer(customer.customer_id)} className="clickable-row">
                <td><div className="customer-cell"><span className="avatar">{customer.customer_id.slice(0, 1).toUpperCase()}</span><span><strong>{customer.customer_id}</strong><small>{customer.internet_service} internet</small></span></div></td>
                <td>{customer.contract}</td><td>{customer.tenure} mo</td><td>${customer.monthly_charges.toFixed(2)}</td>
                <td>{customer.churn == null ? <span className="label-muted">Unlabeled</span> : <span className={`risk-pill ${customer.churn ? "high" : "low"}`}>{customer.churn ? "Churned" : "Active"}</span>}</td>
                <td><span className="row-arrow">→</span></td>
              </tr>
            ))}</tbody>
          </table></div>
        ) : <div className="empty-state">Customer records will appear here after you import a CSV.</div>}
      </section>
    </main>
  );
}
