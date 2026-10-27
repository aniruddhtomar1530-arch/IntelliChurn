import { useCallback, useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CustomerRisk from "./pages/CustomerRisk.jsx";
import Customers from "./pages/Customers.jsx";
import { errorMessage, getCustomers, getDashboard } from "./services/api.js";

export default function App() {
  const [active, setActive] = useState("dashboard");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [summary, records] = await Promise.all([getDashboard(), getCustomers()]);
      setDashboard(summary);
      setCustomers(records);
    } catch (reason) {
      setError(`Could not load the API data: ${errorMessage(reason)}. Check that the backend is running.`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  function navigate(page) {
    setSelectedCustomer(null);
    setActive(page);
  }

  return (
    <div className="app-shell">
      <Sidebar active={active} onNavigate={navigate} />
      <div className="workspace">
        <div className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> {selectedCustomer ? "Customer risk" : active === "dashboard" ? "Overview" : "Customers"}</div>
          <div className="topbar-right"><span className={`api-status ${error ? "offline" : ""}`}><i /> {error ? "API unavailable" : "API workspace"}</span><span className="topbar-avatar">IC</span></div>
        </div>
        {selectedCustomer ? (
          <CustomerRisk customer={selectedCustomer} onBack={() => setSelectedCustomer(null)} />
        ) : active === "customers" ? (
          <Customers
            customers={customers}
            loading={loading}
            error={error}
            onSelectCustomer={(id) => setSelectedCustomer(customers.find((customer) => customer.customer_id === id))}
          />
        ) : (
          <Dashboard
            dashboard={dashboard}
            customers={customers}
            loading={loading}
            error={error}
            reload={reload}
            onSelectCustomer={(id) => setSelectedCustomer(customers.find((customer) => customer.customer_id === id))}
            onViewAll={() => setActive("customers")}
          />
        )}
        <div className="footer-note"><span>Intelligence for better customer relationships</span><span>IntelliChurn · {new Date().getFullYear()}</span></div>
      </div>
    </div>
  );
}
