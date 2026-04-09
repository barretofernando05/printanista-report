import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import FilterPanel from "../components/FilterPanel";
import DataTable from "../components/DataTable";
import DateField from "../components/DateField";

export default function ContadoresPage({ openSerie }) {
  const [filters, setFilters] = useState({
    date_from: "",
    date_to: "",
    client_contains: "",
  });

  const [data, setData] = useState({
    summary: {},
    rows: [],
  });

  const [stacked, setStacked] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const onResize = () => setStacked(window.innerWidth < 1380);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const buildQueryString = () => {
    const qs = new URLSearchParams();

    Object.entries(filters).forEach(([k, v]) => {
      if (v) qs.set(k, v);
    });

    return qs.toString();
  };

  const load = async () => {
    setLoading(true);
    try {
      const qs = buildQueryString();
      const result = await fetchJson(`/api/operaciones/contadores?${qs}`);
      setData(result);
    } catch (error) {
      console.error(error);
      setData({ summary: {}, rows: [] });
    } finally {
      setLoading(false);
    }
  };

  const exportExcel = () => {
    const qs = buildQueryString();
    const url = qs
      ? `/api/operaciones/contadores/export?${qs}`
      : `/api/operaciones/contadores/export`;

    window.open(url, "_blank");
  };

  useEffect(() => {
    load();
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
        <DateField
          label="Desde"
          value={filters.date_from}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, date_from: e.target.value }))
          }
        />

        <DateField
          label="Hasta"
          value={filters.date_to}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, date_to: e.target.value }))
          }
        />

        <Field label="Cliente contiene">
          <input
            value={filters.client_contains}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, client_contains: e.target.value }))
            }
            style={inputStyle}
            placeholder="Ej. BANCO"
          />
        </Field>

        <button onClick={load} style={btnStyle}>
          {loading ? "Cargando..." : "Aplicar"}
        </button>

        <button onClick={exportExcel} style={ghostBtn}>
          Exportar Excel
        </button>
      </FilterPanel>

      <div style={{ minWidth: 0 }}>
        <h1
          style={{
            marginTop: 0,
            fontSize: stacked ? 30 : 42,
            marginBottom: 18,
          }}
        >
          Contadores (BD1)
        </h1>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: stacked ? "1fr 1fr" : "repeat(3, minmax(0, 1fr))",
            gap: 16,
            marginBottom: 16,
          }}
        >
          <Mini title="Series activas" value={data.summary?.series ?? 0} />
          <Mini title="Último día reportado" value={data.summary?.ultimo_reporte ?? "-"} />
          <Mini title="Total registros" value={data.summary?.total ?? 0} />
        </div>

        <div style={panel}>
          <div
            style={{
              fontWeight: 700,
              fontSize: 18,
              marginBottom: 14,
            }}
          >
            Resultados
          </div>

          <DataTable
            rows={data.rows || []}
            pageSize={20}
            onRowClick={(r) =>
              openSerie(
                r.numero_serie ||
                  r.n_mero_serie ||
                  r.serie ||
                  r.numero_serie_idx
              )
            }
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
      <div style={{ fontSize: 22, fontWeight: 800, marginTop: 6 }}>
        {value ?? "-"}
      </div>
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

const ghostBtn = {
  background: "#0b1220",
  color: "#fff",
  border: "1px solid #334155",
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