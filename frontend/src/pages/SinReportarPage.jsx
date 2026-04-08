import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";

const panel = { background: "#101827", border: "1px solid #1f2937", borderRadius: 14, padding: 16 };
const btn = { background: "#ef4444", color: "#fff", border: "none", borderRadius: 10, padding: "10px 14px", fontWeight: 700, cursor: "pointer" };
function Field({ label, children }) { return <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94a3b8" }}><span>{label}</span>{children}</label>; }
function Mini({ title, value }) { return <div style={panel}><div style={{ color: "#94a3b8", fontSize: 12 }}>{title}</div><div style={{ fontSize: 34, fontWeight: 800 }}>{value ?? "-"}</div></div>; }

export default function SinReportarPage({ openSerie }) {
  const [filters, setFilters] = useState({ min_days_no_report: 60, client_contains: "" });
  const [data, setData] = useState({ summary: {}, rows: [] });
  const load = async () => {
    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k,v]) => v !== "" && qs.set(k,v));
    setData(await fetchJson(`/api/operaciones/sin-reportar?${qs.toString()}`));
  };
  useEffect(() => { load().catch(console.error); }, []);
  return <div style={{ display: "flex", gap: 18 }}>
    <FilterPanel title="Parámetros (BD1)">
      <Field label="Mínimo días sin reportar"><input type="number" value={filters.min_days_no_report} onChange={e => setFilters({...filters, min_days_no_report:e.target.value})} /></Field>
      <Field label="Cliente contiene"><input value={filters.client_contains} onChange={e => setFilters({...filters, client_contains:e.target.value})} /></Field>
      <button onClick={load} style={btn}>Generar reporte</button>
    </FilterPanel>
    <div style={{ flex: 1 }}>
      <h1 style={{ marginTop: 0 }}>Equipos sin reportar (BD1)</h1>
      <div style={{ ...panel, marginBottom: 16 }}><div style={{ color: "#94a3b8", fontSize: 12 }}>Equipos que cumplen</div><div style={{ fontSize: 34, fontWeight: 800 }}>{data.summary.total ?? "-"}</div></div>
      <div style={panel}><DataTable rows={data.rows} onRowClick={r => openSerie(r.serie || r.numero_serie || r.numero_serie_idx)} /></div>
    </div>
  </div>;
}
