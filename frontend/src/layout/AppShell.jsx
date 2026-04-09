import React, { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Repeat2,
  Printer,
  Search,
  UploadCloud,
  History,
  Cable,
  Menu,
  X,
  BarChart3,
} from "lucide-react";

const items = [
  ["inicio", "Inicio", LayoutDashboard],
  ["reemplazos", "Reemplazos", Repeat2],
  ["contadores", "Contadores", BarChart3],
  ["sinReportar", "Equipos sin reportar", Printer],
  ["seriesRepetidas", "Series repetidas", Cable],
  ["consulta", "Consulta por serie", Search],
  ["importacion", "Importación / Sync", UploadCloud],
  ["historial", "Historial", History],
];

export default function AppShell({ page, setPage, children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    const onResize = () => {
      setCompact(window.innerWidth < 1350);
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const sidebar = (
    <aside
      style={{
        width: 270,
        minWidth: 270,
        borderRight: "1px solid #111827",
        padding: 20,
        background: "#08111f",
        height: "100vh",
        overflowY: "auto",
      }}
    >
      <div style={{ color: "#ef4444", fontSize: 32, fontWeight: 900 }}>RICOH</div>
      <div style={{ fontSize: 24, fontWeight: 800, marginTop: 4 }}>TECHNOMA</div>
      <div
        style={{
          fontSize: 12,
          color: "#94a3b8",
          marginTop: 14,
          marginBottom: 24,
          letterSpacing: 0.3,
        }}
      >
        PRINTANISTA OPERACIONES
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        {items.map(([key, label, Icon]) => {
          const active = page === key;
          return (
            <button
              key={key}
              onClick={() => {
                setPage(key);
                setMobileOpen(false);
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                width: "100%",
                padding: "14px 16px",
                borderRadius: 14,
                border: "1px solid transparent",
                background: active ? "rgba(239,68,68,0.16)" : "transparent",
                color: "#fff",
                fontWeight: 700,
                cursor: "pointer",
                textAlign: "left",
                fontSize: 17,
              }}
            >
              <Icon size={18} />
              {label}
            </button>
          );
        })}
      </div>
    </aside>
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        background: "#050b16",
        color: "#e5e7eb",
      }}
    >
      {!compact && sidebar}

      {compact && mobileOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(0,0,0,0.45)",
            display: "flex",
          }}
        >
          {sidebar}
          <div style={{ flex: 1 }} onClick={() => setMobileOpen(false)} />
        </div>
      )}

      <main
        style={{
          flex: 1,
          minWidth: 0,
          width: "100%",
          padding: compact ? 16 : 26,
        }}
      >
        {compact && (
          <div
            style={{
              marginBottom: 16,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <button onClick={() => setMobileOpen(true)} style={mobileBtn}>
              <Menu size={18} />
            </button>

            <div style={{ fontWeight: 800, fontSize: 18 }}>Printanista</div>

            <button onClick={() => setMobileOpen(false)} style={mobileBtn}>
              <X size={18} />
            </button>
          </div>
        )}

        <div
          style={{
            width: "100%",
            minWidth: 0,
            maxWidth: "100%",
          }}
        >
          {children}
        </div>
      </main>
    </div>
  );
}

const mobileBtn = {
  background: "#101827",
  color: "#fff",
  border: "1px solid #1f2937",
  borderRadius: 10,
  padding: 10,
  cursor: "pointer",
};