import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import DataTable from "../components/DataTable";

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

  const load = async (activeTab = tab, activeSerie = serie) => {
    if (!activeSerie) return;

    if (activeTab === "resumen") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/resumen`));
    }

    if (activeTab === "insumos") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/insumos`));
    }

    if (activeTab === "alertas") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/alertas`));
    }

    if (activeTab === "reemplazos") {
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/reemplazos`));
    }

    if (activeTab === "contadores") {
      const qs = new URLSearchParams();
      if (dateFrom) qs.set("date_from", dateFrom);
      if (dateTo) qs.set("date_to", dateTo);
      setData(await fetchJson(`/api/serie/${encodeURIComponent(activeSerie)}/contadores?${qs.toString()}`));
    }
  };

  useEffect(() => {
    if (serie) load().catch(console.error);
  }, [tab, serie]);

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
          />
        </label>

        <button
          onClick={() => setSerie(serieInput)}
          style={btnStyle}
        >
          Seleccionar serie
        </button>

        {tab === "contadores" && (
          <>
            <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94a3b8", marginTop: 14 }}>
              <span>Desde</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                style={inputStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94a3b8", marginTop: 10 }}>
              <span>Hasta</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                style={inputStyle}
              />
            </label>

            <button
              onClick={() => load("contadores", serie)}
              style={{ ...btnStyle, marginTop: 10 }}
            >
              Aplicar rango
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
              {{
                resumen: "Resumen (BD3)",
                insumos: "Insumos Detallado (BD3)",
                alertas: "Alertas (BD2)",
                reemplazos: "Reemplazos (BD4)",
                contadores: "Contadores (BD1)",
              }[t]}
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
          {tab === "resumen" && <DataTable rows={data ? [data] : []} />}
          {tab !== "resumen" && <DataTable rows={data.rows || []} />}
        </div>
      </div>
    </div>
  );
}

const inputStyle = {
  background: "#0b1220",
  color: "#fff",
  border: "1px solid #334155",
  borderRadius: 10,
  padding: 10,
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
  marginTop: 10,
};