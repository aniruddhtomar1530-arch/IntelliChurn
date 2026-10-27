import { Activity, LayoutDashboard, UsersRound } from "lucide-react";

export default function Sidebar({ active, onNavigate }) {
  return (
    <aside className="sidebar">
      <a className="brand" href="#" onClick={(event) => event.preventDefault()}>
        <span className="brand-mark"><Activity size={21} /></span>
        <span>intelli<span className="brand-accent">churn</span></span>
      </a>
      <div className="nav-caption">WORKSPACE</div>
      <button className={`nav-item transition-colors ${active === "dashboard" ? "selected" : ""}`} onClick={() => onNavigate("dashboard")}>
        <LayoutDashboard size={18} /> Overview
      </button>
      <button id="customers-nav" className={`nav-item transition-colors ${active === "customers" ? "selected" : ""}`} onClick={() => onNavigate("customers")}>
        <UsersRound size={18} /> Customers
      </button>
      <div className="sidebar-bottom">
        <div className="status-dot" />
        <span>Retention intelligence</span>
        <span className="version">v1.0</span>
      </div>
    </aside>
  );
}
