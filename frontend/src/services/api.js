import axios from "axios";

const api = axios.create({ baseURL: "https://intellichurn.onrender.com/api", timeout: 90000 });

export async function getDashboard() {
  return (await api.get("/dashboard")).data;
}

export async function getCustomers() {
  return (await api.get("/customers", { params: { limit: 100 } })).data;
}

export async function importCustomers(file) {
  const form = new FormData();
  form.append("file", file);
  return (await api.post("/customers/import", form)).data;
}

export async function predictCustomer(customerId) {
  return (
    await api.post(`/customers/${encodeURIComponent(customerId)}/predict`)
  ).data;
}

export async function getPredictions(customerId) {
  return (
    await api.get(`/customers/${encodeURIComponent(customerId)}/predictions`)
  ).data;
}

export async function getRetentionStrategy(request) {
  return (await api.post("/retention-strategy", request)).data;
}

export function errorMessage(error) {
  return error.response?.data?.detail || error.message || "An unexpected error occurred.";
}
