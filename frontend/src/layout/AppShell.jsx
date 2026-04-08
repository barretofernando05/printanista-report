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
} from "lucide-react";

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
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 1200);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const sidebar = (
    <aside
      style={{
        width: isMobile ? 280 : 250,
        minWidth: isMobile ? 280 : 250,
        borderRight: "1px solid #111827",
        padding: 22,
        background: "#0b1220",
        height: "100vh",
        overflowY: "auto",
      }}
    >
      <div style={{ color: "#ef4444", fontSize: 26, fontWeight: 900 }}>RICOH</div>
      <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>TECHNOMA</div>
      <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 16, marginBottom: 22 }}>
        PRINTANISTA OPERACIONES
      </div>

      <div style={{ display: "grid", gap: 8 }}>
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
                gap: 10,
                width: "100%",
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid transparent",
                background: active ? "rgba(239,68,68,0.16)" : "transparent",
                color: "#fff",
                fontWeight: 700,
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <Icon size={16} />
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
        background: "#060b16",
        color: "#e5e7eb",
      }}
    >
      {!isMobile && sidebar}

      {isMobile && mobileOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 50,
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
          padding: isMobile ? 16 : 28,
        }}
      >
        {isMobile && (
          <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
            <button
              onClick={() => setMobileOpen(true)}
              style={{
                background: "#101827",
                color: "#fff",
                border: "1px solid #1f2937",
                borderRadius: 10,
                padding: 10,
                cursor: "pointer",
              }}
            >
              <Menu size={18} />
            </button>
            {mobileOpen && (
              <button
                onClick={() => setMobileOpen(false)}
                style={{
                  background: "#101827",
                  color: "#fff",
                  border: "1px solid #1f2937",
                  borderRadius: 10,
                  padding: 10,
                  cursor: "pointer",
                }}
              >
                <X size={18} />
              </button>
            )}
          </div>
        )}

        <div style={{ width: "100%", minWidth: 0 }}>{children}</div>
      </main>
    </div>
  );
}