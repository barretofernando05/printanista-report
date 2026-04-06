import React, { useState } from "react";
import {
  UploadCloud,
  Search,
  LayoutDashboard,
  Printer,
  Droplet,
  AlertCircle,
  RefreshCw,
  Hash
} from "lucide-react";

export default function App() {
  const [currentView, setCurrentView] = useState("query");
  const [activeTab, setActiveTab] = useState("resumen");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState(null);
  const [searchError, setSearchError] = useState("");

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      alert("Ingresa un número de serie.");
      return;
    }

    setIsSearching(true);
    setSearchError("");
    setResult(null);

    try {
      const response = await fetch(`/api/equipo/${encodeURIComponent(searchQuery.trim())}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "No se encontró el equipo.");
      }

      setResult(data);
    } catch (error) {
      setSearchError(error.message);
    } finally {
      setIsSearching(false);
    }
  };

  const equipo = result?.equipo || {};
  const contadores = result?.contadores || {};
  const alertas = result?.alertas || [];
  const reemplazos = result?.reemplazos || [];

  return (
    <div style={{ minHeight: "100vh", display: "flex" }}>
      <div style={{ width: "260px", background: "#1e293b", color: "#fff", padding: "24px 16px" }}>
        <div style={{ marginBottom: "24px" }}>
          <div style={{ color: "#CF142B", fontWeight: 900, fontSize: "40px" }}>RICOH</div>
          <div style={{ marginTop: "12px", fontSize: "22px", fontWeight: 700 }}>TECHNOMA</div>
        </div>

        <div style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "12px" }}>
          PRINTANISTA DB OPS
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <button onClick={() => setCurrentView("query")} style={navButton(currentView === "query")}>
            <Search size={18} />
            Consultar Equipo
          </button>

          <button onClick={() => setCurrentView("reports")} style={navButton(currentView === "reports")}>
            <LayoutDashboard size={18} />
            Reportes Globales
          </button>
        </div>
      </div>

      <div style={{ flex: 1, padding: "32px", background: "#f8fafc" }}>
        {currentView === "query" && (
          <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
            <h2 style={{ fontSize: "28px", marginBottom: "20px" }}>Consola de Consulta</h2>

            <div style={{ background: "#fff", padding: "20px", borderRadius: "14px", border: "1px solid #e5e7eb", marginBottom: "24px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: 600 }}>
                Buscar por Número de Serie:
              </label>

              <div style={{ display: "flex", gap: "12px" }}>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ej. CN78G9"
                  style={{ flex: 1, padding: "12px", borderRadius: "10px", border: "1px solid #cbd5e1" }}
                />
                <button
                  onClick={handleSearch}
                  style={{ background: "#111827", color: "#fff", border: "none", padding: "12px 18px", borderRadius: "10px", fontWeight: 700 }}
                >
                  {isSearching ? "Buscando..." : "Buscar"}
                </button>
              </div>
            </div>

            {searchError && (
              <div style={{ background: "#fee2e2", color: "#991b1b", padding: "14px", borderRadius: "10px", marginBottom: "20px" }}>
                {searchError}
              </div>
            )}

            {result && (
              <div style={{ background: "#fff", borderRadius: "14px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
                <div style={{ display: "flex", borderBottom: "1px solid #e5e7eb" }}>
                  {[
                    { id: "resumen", icon: Printer, label: "Resumen" },
                    { id: "insumos", icon: Droplet, label: "Insumos" },
                    { id: "alertas", icon: AlertCircle, label: "Alertas" },
                    { id: "reemplazos", icon: RefreshCw, label: "Reemplazos" },
                    { id: "contadores", icon: Hash, label: "Contadores" }
                  ].map((tab) => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={tabStyle(activeTab === tab.id)}>
                      <tab.icon size={16} />
                      {tab.label}
                    </button>
                  ))}
                </div>

                <div style={{ padding: "24px" }}>
                  {activeTab === "resumen" && (
                    <>
                      <h3 style={{ marginTop: 0 }}>Información del Equipo</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
                        {Object.entries(equipo).slice(0, 12).map(([k, v]) => (
                          <Card key={k} label={k} value={String(v ?? "-")} />
                        ))}
                      </div>
                    </>
                  )}

                  {activeTab === "insumos" && (
                    <JsonBlock data={equipo} />
                  )}

                  {activeTab === "alertas" && (
                    <JsonBlock data={alertas} />
                  )}

                  {activeTab === "reemplazos" && (
                    <JsonBlock data={reemplazos} />
                  )}

                  {activeTab === "contadores" && (
                    <JsonBlock data={contadores} />
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {currentView === "reports" && (
          <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", color: "#64748b" }}>
            <LayoutDashboard size={54} />
            <h2>Reportes Globales</h2>
            <p>Aquí luego conectamos búsquedas masivas, duplicados y equipos sin reportar.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function navButton(active) {
  return {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    width: "100%",
    padding: "12px 14px",
    borderRadius: "10px",
    border: "none",
    background: active ? "#ef4444" : "transparent",
    color: "#fff",
    fontWeight: active ? 700 : 500,
    textAlign: "left"
  };
}

function tabStyle(active) {
  return {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "14px 18px",
    border: "none",
    background: active ? "#fef2f2" : "#fff",
    color: active ? "#dc2626" : "#475569",
    fontWeight: 600,
    borderBottom: active ? "2px solid #ef4444" : "2px solid transparent"
  };
}

function Card({ label, value }) {
  return (
    <div style={{ background: "#f8fafc", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "16px" }}>
      <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "6px" }}>{label}</div>
      <div style={{ fontWeight: 700, wordBreak: "break-word" }}>{value}</div>
    </div>
  );
}

function JsonBlock({ data }) {
  return (
    <pre
      style={{
        background: "#0f172a",
        color: "#e2e8f0",
        padding: "16px",
        borderRadius: "12px",
        overflow: "auto",
        fontSize: "13px"
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}