import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";

const panel = { background: "#101827", border: "1px solid #1f2937", borderRadius: 14, padding: 16 };
const btn = { background: "#ef4444", color: "#fff", border: "none", borderRadius: 10, padding: "10px 14px", fontWeight: 700, cursor: "pointer" };
function Field({ label, children }) { return <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94a3b8" }}><span>{label}</span>{children}</label>; }
function Mini({ title, value }) { return <div style={panel}><div style={{ color: "#94a3b8", fontSize: 12 }}>{title}</div><div style={{ fontSize: 34, fontWeight: 800 }}>{value ?? "-"}</div></div>; }

export default function SeriesRepetidasPage({ openSerie }) {
  const [filters, setFilters] = useState({ min_distinct_clients: 2, active_last_days: 90 });
  const [data, setData] = useState({ summary: {}, rows: [] });
  const [selectedSerie, setSelectedSerie] = useState("");
  const [clients, setClients] = useState([]);
  const load = async () => {
    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k,v]) => qs.set(k,v));
    setData(await fetchJson(`/api/operaciones/series-repetidas?${qs.toString()}`));
  };
  const loadClients = async (serie) => {
    setSelectedSerie(serie);
    const r = await fetchJson(`/api/operaciones/series-repetidas/${encodeURIComponent(serie)}/clientes`);
    setClients(r.rows || []);
  };
  useEffect(() => { load().catch(console.error); }, []);
  return <div style={{ display: "flex", gap: 18 }}>
    <FilterPanel title="Parámetros (BD1 - Series)">
      <Field label="Mínimo clientes distintos"><input type="number" value={filters.min_distinct_clients} onChange={e => setFilters({...filters, min_distinct_clients:e.target.value})} /></Field>
      <Field label="Activa últimos días"><input type="number" value={filters.active_last_days} onChange={e => setFilters({...filters, active_last_days:e.target.value})} /></Field>
      <button onClick={load} style={btn}>Generar reporte</button>
    </FilterPanel>
    <div style={{ flex: 1 }}>
      <h1 style={{ marginTop: 0 }}>Series repetidas (BD1) + Clientes</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 16 }}>
        <Mini title="Series mostradas" value={data.summary.series} />
        <Mini title="Serie seleccionada" value={selectedSerie || "-"} />
        <Mini title="Clientes asociados" value={clients.length} />
      </div>
      <div style={{ ...panel, marginBottom: 18 }}><DataTable rows={data.rows} onRowClick={r => loadClients(r.serie || r.numero_serie || r.numero_serie_idx)} /></div>
      <div style={panel}><div style={{ fontWeight: 700, marginBottom: 10 }}>Clientes asignados a la serie seleccionada</div><DataTable rows={clients} onRowClick={r => openSerie(r.serie || selectedSerie)} /></div>
    </div>
  </div>;
}
