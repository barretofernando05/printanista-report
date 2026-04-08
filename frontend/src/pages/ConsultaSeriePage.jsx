import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import DataTable from "../components/DataTable";
import DateField from "../components/DateField";

const tabs = ["resumen", "insumos", "alertas", "reemplazos", "contadores"];

export default function ConsultaSeriePage({ serie, setSerie }) {
  const [tab, setTab] = useState("resumen");
  const [serieInput, setSerieInput] = useState(serie || "");
  const [data, setData] = useState({});
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [stacked, setStacked] = useState(false);

  useEffect(() => {
    const onResize = () => setStacked(window.innerWidth < 1300);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const load = async (activeTab = tab, activeSerie = serie, from = dateFrom, to = dateTo) => {
    if (!activeSerie) return;

    if (activeTab === "resumen") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/resumen`));
      return;
    }

    if (activeTab === "insumos") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/insumos`));
      return;
    }

    if (activeTab === "alertas") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/alertas`));
      return;
    }

    if (activeTab === "reemplazos") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/reemplazos`));
      return;
    }

    if (activeTab === "contadores") {
      const qs = new URLSearchParams();
      if (from) qs.set("date_from", from);
      if (to) qs.set("date_to", to);

      setData(
        await fetchJson(
          `/api/serie/${encodeURIComponent(activeSerie)}/contadores?${qs.toString()}`
        )
      );
    }
  };

  useEffect(() => {
    if (serie) {
      load().catch(console.error);
    }
  }, [tab, serie]);

  const applyQuickRange = (days) => {
    const today = new Date();
    const end = formatDate(today);
    const startDate = new Date();
    startDate.setDate(today.getDate() - days);
    const start = formatDate(startDate);

    setDateFrom(start);
    setDateTo(end);

    if (serie && tab === "contadores") {
      load("contadores", serie, start, end).catch(console.error);
    }
  };

  const applyThisMonth = () => {
    const today = new Date();
    const start = formatDate(new Date(today.getFullYear(), today.getMonth(), 1));
    const end = formatDate(today);

    setDateFrom(start);
    setDateTo(end);

    if (serie && tab === "contadores") {
      load("contadores", serie, start, end).catch(console.error);
    }
  };

  const clearRange = () => {
    setDateFrom("");
    setDateTo("");

    if (serie && tab === "contadores") {
      load("contadores", serie, "", "").catch(console.error);
    }
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: stacked ? "1fr" : "280px minmax(0, 1fr)",
        gap: 18,
        alignItems: "start",
      }}
    >
      <aside
        style={{
          background: "#111827",
          border: "1px solid #1f2937",
          borderRadius: 14,
          padding: 16,
          alignSelf: "start",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 14 }}>Conexión / Filtro</div>

        <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94a3b8" }}>
          <span>Buscar parte de la serie</span>
          <input
            value={serieInput}
            onChange={(e) => setSerieInput(e.target.value)}
            style={inputStyle}
            placeholder="Ej. A0D5P502112"
          />
        </label>

        <button onClick={() => setSerie(serieInput)} style={btnStyle}>
          Seleccionar serie
        </button>

        {tab === "contadores" && (
          <>
            <div style={{ marginTop: 14 }}>
              <DateField
                label="Desde"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>

            <div style={{ marginTop: 10 }}>
              <DateField
                label="Hasta"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
                marginTop: 12,
              }}
            >
              <button style={quickBtn} onClick={() => applyQuickRange(0)}>
                Hoy
              </button>
              <button style={quickBtn} onClick={() => applyQuickRange(7)}>
                7 días
              </button>
              <button style={quickBtn} onClick={() => applyQuickRange(30)}>
                30 días
              </button>
              <button style={quickBtn} onClick={applyThisMonth}>
                Este mes
              </button>
            </div>

            <button
              onClick={() => load("contadores", serie)}
              style={{ ...btnStyle, marginTop: 12 }}
            >
              Aplicar rango
            </button>

            <button
              onClick={clearRange}
              style={{ ...ghostBtn, marginTop: 10 }}
            >
              Limpiar rango
            </button>
          </>
        )}
      </aside>

      <div style={{ minWidth: 0 }}>
        <h1
          style={{
            marginTop: 0,
            fontSize: stacked ? 28 : 36,
            lineHeight: 1.1,
            marginBottom: 16,
          }}
        >
          Printanista - Consola de Consulta (BD1/BD2/BD3/BD4)
        </h1>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 10,
            marginBottom: 16,
            borderBottom: "1px solid #1f2937",
            paddingBottom: 10,
          }}
        >
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                background: "transparent",
                border: "none",
                color: tab === t ? "#ef4444" : "#cbd5e1",
                cursor: "pointer",
                fontWeight: 700,
                padding: 0,
              }}
            >
              {tabLabel(t)}
            </button>
          ))}
        </div>

        <div
          style={{
            background: "#101827",
            border: "1px solid #1f2937",
            borderRadius: 14,
            padding: 16,
            minWidth: 0,
          }}
        >
          {tab === "resumen" ? (
            <DataTable rows={data ? [data] : []} />
          ) : (
            <DataTable rows={data.rows || []} />
          )}
        </div>
      </div>
    </div>
  );
}

function tabLabel(t) {
  const labels = {
    resumen: "Resumen (BD3)",
    insumos: "Insumos Detallado (BD3)",
    alertas: "Alertas (BD2)",
    reemplazos: "Reemplazos (BD4)",
    contadores: "Contadores (BD1)",
  };
  return labels[t] || t;
}

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const inputStyle = {
  background: "#0b1220",
  color: "#fff",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: "10px 12px",
  width: "100%",
};

const btnStyle = {
  background: "#ef4444",
  color: "#fff",
  border: "none",
  borderRadius: 10,
  padding: "10px 14px",
  fontWeight: 700,
  cursor: "pointer",
};

const ghostBtn = {
  background: "#0b1220",
  color: "#e5e7eb",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: "10px 14px",
  fontWeight: 700,
  cursor: "pointer",
  width: "100%",
};

const quickBtn = {
  background: "#0b1220",
  color: "#cbd5e1",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: "9px 10px",
  fontWeight: 700,
  cursor: "pointer",
};