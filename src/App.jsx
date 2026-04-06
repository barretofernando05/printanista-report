import React, { useState } from "react";
import {
  UploadCloud,
  Search,
  FileText,
  LayoutDashboard,
  Printer,
  Droplet,
  AlertCircle,
  RefreshCw,
  Hash,
  Bot,
  Settings
} from "lucide-react";

export default function App() {
  const [currentView, setCurrentView] = useState("query");
  const [mode, setMode] = useState("auto");
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const [activeTab, setActiveTab] = useState("resumen");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [equipmentData, setEquipmentData] = useState(null);
  const [searchError, setSearchError] = useState("");

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.length > 0) {
      setFiles((prev) => [...prev, ...Array.from(e.dataTransfer.files)]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files?.length > 0) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files)]);
    }
  };

  const handleProcess = async () => {
    if (!files.length) {
      alert("Sube al menos un archivo.");
      return;
    }

    setIsUploading(true);
    setUploadMessage("");

    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al procesar archivos");
      }

      setUploadMessage(`Carga exitosa. Filas procesadas: ${data.rows_processed}`);
      setFiles([]);
    } catch (error) {
      setUploadMessage(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      alert("Ingresa un número de serie.");
      return;
    }

    setIsSearching(true);
    setSearchError("");
    setEquipmentData(null);

    try {
      const response = await fetch(`/api/records/${encodeURIComponent(searchQuery.trim())}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "No se encontró el equipo.");
      }

      setEquipmentData(data);
    } catch (error) {
      setSearchError(error.message);
    } finally {
      setIsSearching(false);
    }
  };

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
          <button onClick={() => setCurrentView("import")} style={navButton(currentView === "import")}>
            <UploadCloud size={18} />
            Importar Datos
          </button>

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
        {currentView === "import" && (
          <div style={{ maxWidth: "900px", margin: "0 auto" }}>
            <h2 style={{ fontSize: "32px", marginBottom: "8px" }}>Carga de Archivos</h2>
            <p style={{ color: "#64748b", marginBottom: "24px" }}>
              Sube los reportes diarios (.xlsx, .csv) para poblar MariaDB.
            </p>

            <div style={{ display: "flex", gap: "24px", marginBottom: "24px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input type="radio" checked={mode === "auto"} onChange={() => setMode("auto")} />
                <Bot size={18} />
                Automático
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input type="radio" checked={mode === "manual"} onChange={() => setMode("manual")} />
                <Settings size={18} />
                Manual
              </label>
            </div>

            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => document.getElementById("fileUpload").click()}
              style={{
                border: "2px dashed #94a3b8",
                background: "#fff",
                padding: "40px",
                borderRadius: "16px",
                textAlign: "center",
                cursor: "pointer",
                marginBottom: "20px"
              }}
            >
              <input
                id="fileUpload"
                type="file"
                multiple
                accept=".xlsx,.xls,.csv"
                style={{ display: "none" }}
                onChange={handleFileSelect}
              />
              <UploadCloud size={50} style={{ marginBottom: "12px", color: "#64748b" }} />
              <p style={{ fontSize: "18px", fontWeight: 600, margin: 0 }}>Arrastra los archivos aquí</p>
              <p style={{ color: "#64748b" }}>o haz clic para seleccionarlos</p>
            </div>

            {files.length > 0 && (
              <div style={{ background: "#fff", borderRadius: "12px", padding: "16px", border: "1px solid #e5e7eb", marginBottom: "20px" }}>
                {files.map((file, idx) => (
                  <div key={idx} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 0" }}>
                    <FileText size={16} />
                    {file.name}
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={handleProcess}
              disabled={isUploading}
              style={{
                background: "#ef4444",
                color: "#fff",
                border: "none",
                padding: "14px 20px",
                borderRadius: "10px",
                fontWeight: 700
              }}
            >
              {isUploading ? "Procesando..." : "Importar a MariaDB"}
            </button>

            {uploadMessage && <div style={{ marginTop: "20px", fontWeight: 600 }}>{uploadMessage}</div>}
          </div>
        )}

        {currentView === "query" && (
          <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
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
                  Buscar
                </button>
              </div>
            </div>

            {searchError && (
              <div style={{ background: "#fee2e2", color: "#991b1b", padding: "14px", borderRadius: "10px", marginBottom: "20px" }}>
                {searchError}
              </div>
            )}

            {equipmentData && !isSearching && (
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
                  {activeTab === "resumen" ? (
                    <>
                      <h3 style={{ marginTop: 0 }}>Información del Equipo</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "24px" }}>
                        <Card label="Número de Serie" value={equipmentData.serial} />
                        <Card label="Fabricante" value={equipmentData.manufacturer || "-"} />
                        <Card label="Modelo" value={equipmentData.model || "-"} />
                        <Card label="Cliente / Cuenta" value={equipmentData.client || "-"} />
                        <Card label="Dirección IP" value={equipmentData.ip_address || "-"} />
                        <Card label="Último Reporte" value={equipmentData.last_report || "-"} />
                      </div>

                      <h3>Contadores Actuales</h3>
                      <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                        <CounterCard title="Total Mono" value={equipmentData.total_mono || "0"} />
                        <CounterCard title="Total Color" value={equipmentData.total_color || "0"} />
                      </div>
                    </>
                  ) : (
                    <div style={{ color: "#64748b" }}>
                      Esta sección queda preparada para conectar más tablas desde MariaDB.
                    </div>
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
            <p>Aquí luego conectamos reportes masivos, duplicados, equipos sin reportar, etc.</p>
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
      <div style={{ fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function CounterCard({ title, value }) {
  return (
    <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "12px", padding: "18px", minWidth: "240px" }}>
      <div style={{ fontWeight: 600, marginBottom: "8px" }}>{title}</div>
      <div style={{ fontSize: "28px", fontWeight: 800 }}>{value}</div>
    </div>
  );
}