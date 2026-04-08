import React from "react";
import { LayoutDashboard, Repeat2, Printer, Search, UploadCloud, History, Cable } from "lucide-react";

const items = [
  ["inicio", "Inicio", LayoutDashboard],
  ["reemplazos", "Reemplazos", Repeat2],
  ["sinReportar", "Equipos sin reportar", Printer],
  ["seriesRepetidas", "Series repetidas", Cable],
  ["consulta", "Consulta por serie", Search],
  ["importacion", "Importación / Sync", UploadCloud],
  ["historial", "Historial", History],
];

export default function AppShell({ page, setPage, children }) {
  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "#060b16", color: "#e5e7eb" }}>
      <aside style={{ width: 260, borderRight: "1px solid #111827", padding: 22, background: "#0b1220" }}>
        <div style={{ color: "#ef4444", fontSize: 26, fontWeight: 900 }}>RICOH</div>
        <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>TECHNOMA</div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 16, marginBottom: 22 }}>PRINTANISTA OPERACIONES</div>
        <div style={{ display: "grid", gap: 8 }}>
          {items.map(([key, label, Icon]) => {
            const active = page === key;
            return (
              <button key={key} onClick={() => setPage(key)} style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "12px 14px", borderRadius: 12, border: "1px solid transparent", background: active ? "rgba(239,68,68,0.16)" : "transparent", color: "#fff", fontWeight: 700, cursor: "pointer", textAlign: "left" }}>
                <Icon size={16} />
                {label}
              </button>
            );
          })}
        </div>
      </aside>
      <main style={{ flex: 1, padding: 28 }}>{children}</main>
    </div>
  );
}
