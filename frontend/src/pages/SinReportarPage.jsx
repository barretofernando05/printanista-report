import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";

export default function SinReportarPage({ openSerie }) {
  const [filters, setFilters] = useState({
    min_days_no_report: 60,
    client_contains: "",
  });

  const [data, setData] = useState({
    summary: {},
    rows: [],
  });

  const [stacked, setStacked] = useState(false);

  useEffect(() => {
    const onResize = () => setStacked(window.innerWidth < 1380);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const load = async () => {
    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== "") qs.set(k, v);
    });

    setData(await fetchJson(`/api/operaciones/sin-reportar?${qs.toString()}`));
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: stacked ? "1fr" : "300px minmax(0, 1fr)",
        gap: 18,
        alignItems: "start",
      }}
    >
      <FilterPanel title="Parámetros (BD1)">
        <Field label="Mínimo días sin reportar">
          <input
            type="number"
            value={filters.min_days_no_report}
            onChange={(e) => setFilters({ ...filters, min_days_no_report: e.target.value })}
            style={inputStyle}
          />
        </Field>

        <Field label="Cliente contiene">
          <input
            value={filters.client_contains}
            onChange={(e) => setFilters({ ...filters, client_contains: e.target.value })}
            style={inputStyle}
          />
        </Field>

        <button onClick={load} style={btnStyle}>
          Generar reporte
        </button>
      </FilterPanel>

      <div style={{ minWidth: 0 }}>
        <h1 style={{ marginTop: 0, fontSize: stacked ? 30 : 42 }}>
          Equipos sin reportar (BD1)
        </h1>

        <div style={{ ...panel, marginBottom: 16 }}>
          <div style={{ color: "#94a3b8", fontSize: 13 }}>Equipos que cumplen</div>
          <div style={{ fontSize: 22, fontWeight: 800, marginTop: 6 }}>
            {data.summary.total ?? "-"}
          </div>
        </div>

        <div style={panel}>
          <DataTable
            rows={data.rows}
            pageSize={20}
            onRowClick={(r) => openSerie(r.serie || r.numero_serie || r.numero_serie_idx)}
          />
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span style={{ fontSize: 13, color: "#cbd5e1" }}>{label}</span>
      {children}
    </label>
  );
}

const panel = {
  background: "#101827",
  border: "1px solid #1f2937",
  borderRadius: 14,
  padding: 16,
};

const btnStyle = {
  background: "#ef4444",
  color: "#fff",
  border: "none",
  borderRadius: 12,
  padding: "12px 16px",
  fontWeight: 700,
  cursor: "pointer",
};

const inputStyle = {
  background: "#0b1220",
  color: "#fff",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: "10px 12px",
  width: "100%",
};