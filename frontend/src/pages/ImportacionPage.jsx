import React, { useState } from "react";
import { fetchJson } from "../api";

export default function ImportacionPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function upload(kind, file) {
    if (!file) return;
    setError(""); setMessage("");
    try {
      const fd = new FormData(); fd.append("file", file);
      const data = await fetchJson(`/api/import/${kind}`, { method: "POST", body: fd });
      setMessage(JSON.stringify(data, null, 2));
    } catch (e) { setError(e.message); }
  }
  async function sync(kind) {
    setError(""); setMessage("");
    try {
      const data = await fetchJson(`/api/sync/${kind}`, { method: "POST" });
      setMessage(JSON.stringify(data, null, 2));
    } catch (e) { setError(e.message); }
  }
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Importación / Sync</h1>
      {error && <div style={{ background: "#7f1d1d", padding: 12, borderRadius: 10, marginBottom: 16 }}>{error}</div>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 18 }}>
        <Panel title="Importar BD1"><input type="file" accept=".xlsx,.csv" onChange={(e) => upload("bd1", e.target.files?.[0])} /></Panel>
        <Panel title="Importar BD3"><input type="file" accept=".xlsx,.csv" onChange={(e) => upload("bd3", e.target.files?.[0])} /></Panel>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <Panel title="Gmail Sync">
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {["bd1","bd2","bd3","bd4","all"].map((k) => <button key={k} onClick={() => sync(k)} style={{ background: "#ef4444", color: "#fff", border: "none", borderRadius: 10, padding: "10px 14px", fontWeight: 700, cursor: "pointer" }}>Sync {k.toUpperCase()}</button>)}
          </div>
        </Panel>
        <Panel title="Resultado"><pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{message || "Todavía no hay resultados."}</pre></Panel>
      </div>
    </div>
  );
}
function Panel({ title, children }) {
  return <div style={{ background: "#101827", border: "1px solid #1f2937", borderRadius: 14, padding: 16 }}><div style={{ fontWeight: 700, marginBottom: 10 }}>{title}</div>{children}</div>;
}
