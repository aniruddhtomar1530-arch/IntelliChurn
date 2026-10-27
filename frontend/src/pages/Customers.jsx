import { useMemo, useState } from "react";
import { Search } from "lucide-react";

export default function Customers({ customers, loading, error, onSelectCustomer }) {
  const [query, setQuery] = useState("");
  const filteredCustomers = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return customers;
    return customers.filter((customer) =>
      [customer.customer_id, customer.contract, customer.internet_service]
        .some((value) => value.toLowerCase().includes(normalized)),
    );
  }, [customers, query]);

  return (
    <main className="main-content">
      <header className="page-header">
        <div>
          <div className="eyebrow">CUSTOMER MANAGEMENT</div>
          <h1>Customers</h1>
          <p>Browse your imported customer records and assess churn risk.</p>
        </div>
        <label className="search-control">
          <Search size={15} />
          <input
            aria-label="Search customers"
            placeholder="Search customers"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </header>
      {error && <div className="notice notice-error">{error}</div>}
      <section className="panel table-panel directory-panel">
        <div className="panel-heading table-heading">
          <div><h2>Customer directory</h2><p>Showing {filteredCustomers.length} of {customers.length} loaded records</p></div>
        </div>
        {loading && !customers.length ? <div className="empty-state">Loading customer data…</div> : filteredCustomers.length ? (
          <div className="table-scroll"><table>
            <thead><tr><th>Customer</th><th>Contract</th><th>Tenure</th><th>Monthly charges</th><th>Churn label</th><th></th></tr></thead>
            <tbody>{filteredCustomers.map((customer) => (
              <tr key={customer.customer_id} onClick={() => onSelectCustomer(customer.customer_id)} className="clickable-row">
                <td><div className="customer-cell"><span className="avatar">{customer.customer_id.slice(0, 1).toUpperCase()}</span><span><strong>{customer.customer_id}</strong><small>{customer.internet_service} internet</small></span></div></td>
                <td>{customer.contract}</td><td>{customer.tenure} mo</td><td>${customer.monthly_charges.toFixed(2)}</td>
                <td>{customer.churn == null ? <span className="label-muted">Unlabeled</span> : <span className={`risk-pill ${customer.churn ? "high" : "low"}`}>{customer.churn ? "Churned" : "Active"}</span>}</td>
                <td><span className="row-arrow">→</span></td>
              </tr>
            ))}</tbody>
          </table></div>
        ) : <div className="empty-state">{query ? "No customers match your search." : "Import a customer CSV to populate this directory."}</div>}
      </section>
    </main>
  );
}
