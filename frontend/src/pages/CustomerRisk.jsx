import { useEffect, useState } from "react";
import { ArrowLeft, BrainCircuit, LoaderCircle, Sparkles } from "lucide-react";
import {
  errorMessage,
  getPredictions,
  getRetentionStrategy,
  predictCustomer,
} from "../services/api.js";

export default function CustomerRisk({ customer, onBack }) {
  const [predictions, setPredictions] = useState([]);
  const [activePrediction, setActivePrediction] = useState(null);
  const [busy, setBusy] = useState(false);
  const [strategy, setStrategy] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const items = await getPredictions(customer.customer_id);
      setPredictions(items);
      setActivePrediction(items[0] || null);
    } catch (reason) {
      setError(errorMessage(reason));
    }
  }

  useEffect(() => { load(); }, [customer.customer_id]);

  async function runPrediction() {
    setBusy(true);
    setError("");
    setStrategy("");
    try {
      const prediction = await predictCustomer(customer.customer_id);
      setActivePrediction(prediction);
      await load();
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  async function makeStrategy() {
    if (!activePrediction) return;
    setBusy(true);
    setError("");
    try {
      const result = await getRetentionStrategy({
        customer,
        churn_probability: activePrediction.churn_probability,
        factors: activePrediction.explanation,
      });
      setStrategy(result.strategy);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  const probability = activePrediction?.churn_probability;
  return (
    <main className="main-content">
      <button className="back-button" onClick={onBack}><ArrowLeft size={16} /> Back to customers</button>
      <header className="page-header customer-header">
        <div><div className="eyebrow">CUSTOMER PROFILE</div><h1>{customer.customer_id}</h1><p>{customer.contract} contract · customer for {customer.tenure} months</p></div>
        <button className="button button-primary" onClick={runPrediction} disabled={busy}><BrainCircuit size={16} /> {busy ? "Analyzing…" : "Run risk analysis"}</button>
      </header>
      {error && <div className="notice notice-error">{error}</div>}

      <section className="risk-layout">
        <article className="panel risk-score-panel">
          <div className="panel-heading"><div><h2>Churn probability</h2><p>Latest model assessment</p></div><span className="score-icon"><BrainCircuit size={19} /></span></div>
          {probability == null ? <div className="risk-empty"><p>No assessment available yet.</p><button className="button button-primary" onClick={runPrediction} disabled={busy}>Run first prediction</button></div> : <>
            <div className={`big-probability ${activePrediction.risk_level.toLowerCase()}`}>{(probability * 100).toFixed(1)}<span>%</span></div>
            <span className={`risk-pill ${activePrediction.risk_level.toLowerCase()}`}>{activePrediction.risk_level} risk</span>
            <p className="risk-context">Prediction recorded {new Date(activePrediction.created_at).toLocaleString()}</p>
          </>}
          <div className="customer-facts">
            <div><span>Monthly charges</span><strong>${customer.monthly_charges.toFixed(2)}</strong></div>
            <div><span>Total charges</span><strong>${customer.total_charges.toFixed(2)}</strong></div>
            <div><span>Internet</span><strong>{customer.internet_service}</strong></div>
            <div><span>Payment</span><strong>{customer.payment_method}</strong></div>
          </div>
        </article>

        <article className="panel factors-panel">
          <div className="panel-heading"><div><h2>What drives this score?</h2><p>SHAP feature contributions · positive increases risk</p></div></div>
          {activePrediction?.explanation?.length ? <div className="factor-list">{activePrediction.explanation.map((factor) => (
            <div className="factor-row" key={factor.feature}>
              <span className="factor-name">{factor.feature.replaceAll("_", " ")}</span>
              <span className="factor-track"><span className={factor.impact >= 0 ? "factor-positive" : "factor-negative"} style={{ width: `${Math.min(100, Math.max(8, Math.abs(factor.impact) * 100))}%` }} /></span>
              <span className={`factor-value ${factor.impact >= 0 ? "text-orange" : "text-green"}`}>{factor.impact > 0 ? "+" : ""}{factor.impact.toFixed(3)}</span>
            </div>
          ))}</div> : <div className="empty-state">Run a prediction to see the strongest churn drivers.</div>}
          <div className="factor-legend"><span><i className="legend-positive" /> Increases risk</span><span><i className="legend-negative" /> Reduces risk</span></div>
        </article>
      </section>

      <section className="panel strategy-panel">
        <div className="strategy-title"><span className="strategy-icon"><Sparkles size={19} /></span><div><h2>AI retention playbook</h2><p>Personalized ideas informed by this customer’s risk drivers</p></div></div>
        {strategy ? <div className="strategy-copy">{strategy.split("\n").filter(Boolean).map((line, index) => <p key={`${index}-${line}`}>{line}</p>)}</div> : <p className="strategy-placeholder">Generate an actionable retention strategy using Gemini. Requires a configured API key.</p>}
        <button className="button button-soft" onClick={makeStrategy} disabled={busy || !activePrediction}><Sparkles size={15} /> {busy ? <><LoaderCircle className="spin" size={15} /> Working…</> : "Generate strategy"}</button>
      </section>
    </main>
  );
}
