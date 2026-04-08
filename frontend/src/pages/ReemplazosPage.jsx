import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";

const panel = { background: "#101827", border: "1px solid #1f2937", borderRadius: 14, padding: 16 };
const btn = { background: "#ef4444", color: "#fff", border: "none", borderRadius: 10, padding: "10px 14px", fontWeight: 700, cursor: "pointer" };
function Field({ label, children }) { return <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94a3b8" }}><span>{label}</span>{children}</label>; }
function Mini({ title, value }) { return <div style={panel}><div style={{ color: "#94a3b8", fontSize: 12 }}>{title}</div><div style={{ fontSize: 34, fontWeight: 800 }}>{value ?? "-"}</div></div>; }

export default function ReemplazosPage({ openSerie }) {
  const [filters, setFilters] = useState({ date_from: "", date_to: "", client_contains: "" });
  const [data, setData] = useState({ summary: {}, rows: [] });
  const load = async () => {
    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k,v]) => v && qs.set(k,v));
    setData(await fetchJson(`/api/operaciones/reemplazos?${qs.toString()}`));
  };
  useEffect(() => { load().catch(console.error); }, []);
  return <div style={{ display: "flex", gap: 18 }}>
    <FilterPanel title="Parámetros (BD3)">
      <Field label="Desde"><input type="date" value={filters.date_from} onChange={e => setFilters({...filters, date_from:e.target.value})} /></Field>
      <Field label="Hasta"><input type="date" value={filters.date_to} onChange={e => setFilters({...filters, date_to:e.target.value})} /></Field>
      <Field label="Cliente contiene"><input value={filters.client_contains} onChange={e => setFilters({...filters, client_contains:e.target.value})} /></Field>
      <button onClick={load} style={btn}>Ejecutar análisis</button>
    </FilterPanel>
    <div style={{ flex: 1 }}>
      <h1 style={{ marginTop: 0 }}>Reemplazos (BD3)</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 16 }}>
        <Mini title="Eventos" value={data.summary.eventos} />
        <Mini title="Innecesarios" value={data.summary.innecesarios} />
        <Mini title="No nuevos" value={data.summary.no_nuevos} />
        <Mini title="Sin alerta" value={data.summary.sin_alerta} />
      </div>
      <div style={panel}>
        <DataTable rows={data.rows} onRowClick={r => openSerie(r.numero_serie || r.serie || r.numero_serie_txt)} />
      </div>
    </div>
  </div>;
}
