import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";

export default function InicioPage({ openPage, setSerie }) {
  const [data, setData] = useState(null);
  const [serieInput, setSerieInput] = useState("");
  useEffect(() => { fetchJson("/api/dashboard/home").then(setData).catch(console.error); }, []);
  return (
    <div>
      <h1 style={{ marginTop: 0, fontSize: 42 }}>Consola Printanista</h1>
      <div style={{ color: "#94a3b8", marginBottom: 24 }}>Base operativa, consulta por serie, importación y reportes.</div>
      <div style={{ background: "#101827", border: "1px solid #1f2937", borderRadius: 14, padding: 18, marginBottom: 18 }}>
        <div style={{ fontWeight: 700, marginBottom: 10 }}>Búsqueda rápida por serie</div>
        <div style={{ display: "flex", gap: 10 }}>
          <input value={serieInput} onChange={(e) => setSerieInput(e.target.value)} placeholder="Ej. T926Q130031" style={{ flex: 1, background: "#0b1220", color: "#fff", border: "1px solid #334155", borderRadius: 10, padding: 12 }} />
          <button onClick={() => { setSerie(serieInput); openPage("consulta"); }} style={{ background: "#ef4444", color: "#fff", border: "none", borderRadius: 10, padding: "12px 18px", fontWeight: 700 }}>Abrir</button>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0,1fr))", gap: 16, marginBottom: 18 }}>
        <Card title="Sin reportar" value={data?.quick?.sin_reportar ?? "-"} onClick={() => openPage("sinReportar")} />
        <Card title="Reemplazos recientes" value={data?.quick?.reemplazos_recientes ?? "-"} onClick={() => openPage("reemplazos")} />
        <Card title="Series repetidas" value={data?.quick?.series_repetidas ?? "-"} onClick={() => openPage("seriesRepetidas")} />
        <Card title="Importación / Sync" value="Abrir" onClick={() => openPage("importacion")} />
      </div>
    </div>
  );
}

function Card({ title, value, onClick }) {
  return <button onClick={onClick} style={{ background: "#101827", color: "#fff", border: "1px solid #1f2937", borderRadius: 14, padding: 18, textAlign: "left", cursor: "pointer" }}><div style={{ color: "#94a3b8", fontSize: 13 }}>{title}</div><div style={{ fontSize: 28, fontWeight: 800, marginTop: 8 }}>{value}</div></button>;
}
