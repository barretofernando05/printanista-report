import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";

export default function SeriesRepetidasPage({ openSerie }) {
  const [filters, setFilters] = useState({
    min_distinct_clients: 2,
    active_last_days: 90,
  });

  const [data, setData] = useState({
    summary: {},
    rows: [],
  });

  const [selectedSerie, setSelectedSerie] = useState("");
  const [clients, setClients] = useState([]);
  const [stacked, setStacked] = useState(false);

  useEffect(() => {
    const onResize = () => setStacked(window.innerWidth < 1380);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const load = async () => {
    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => qs.set(k, v));
    setData(await fetchJson(`/api/operaciones/series-repetidas?${qs.toString()}`));
  };

  const loadClients = async (serie) => {
    setSelectedSerie(serie);
    const result = await fetchJson(
      `/api/operaciones/series-repetidas/${encodeURIComponent(serie)}/clientes`
    );
    setClients(result.rows || []);
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
      <FilterPanel title="Parámetros (BD1 - Series)">
        <Field label="Mínimo clientes distintos">
          <input
            type="number"
            value={filters.min_distinct_clients}
            onChange={(e) =>
              setFilters({ ...filters, min_distinct_clients: e.target.value })
            }
            style={inputStyle}
          />
        </Field>

        <Field label="Activa últimos días">
          <input
            type="number"
            value={filters.active_last_days}
            onChange={(e) => setFilters({ ...filters, active_last_days: e.target.value })}
            style={inputStyle}
          />
        </Field>

        <button onClick={load} style={btnStyle}>
          Generar reporte
        </button>
      </FilterPanel>

      <div style={{ minWidth: 0 }}>
        <h1 style={{ marginTop: 0, fontSize: stacked ? 30 : 42 }}>
          Series repetidas (BD1) + Clientes
        </h1>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: stacked ? "1fr" : "repeat(3, minmax(0, 1fr))",
            gap: 16,
            marginBottom: 16,
          }}
        >
          <Mini title="Series mostradas" value={data.summary.series} />
          <Mini title="Serie seleccionada" value={selectedSerie || "-"} />
          <Mini title="Clientes asociados" value={clients.length} />
        </div>

        <div style={{ ...panel, marginBottom: 18 }}>
          <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 14 }}>
            Series
          </div>
          <DataTable
            rows={data.rows}
            pageSize={20}
            onRowClick={(r) =>
              loadClients(r.serie || r.numero_serie || r.numero_serie_idx)
            }
          />
        </div>

        <div style={panel}>
          <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 14 }}>
            Clientes asignados a la serie seleccionada
          </div>
          <DataTable
            rows={clients}
            pageSize={15}
            onRowClick={(r) => openSerie(r.serie || selectedSerie)}
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

function Mini({ title, value }) {
  return (
    <div style={panel}>
      <div style={{ color: "#94a3b8", fontSize: 13 }}>{title}</div>
      <div style={{ fontSize: 22, fontWeight: 800, marginTop: 6 }}>{value ?? "-"}</div>
    </div>
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