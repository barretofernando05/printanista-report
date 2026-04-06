import React, { useMemo, useState } from "react";
import {
  Search, LayoutDashboard, Printer, Droplet, AlertCircle, RefreshCw, Hash,
  ServerCrash, UploadCloud, MailCheck
} from "lucide-react";

export default function App() {
  const [currentView, setCurrentView] = useState("query");
  const [activeTab, setActiveTab] = useState("resumen");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState(null);
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState([]);
  const [uploading, setUploading] = useState({ bd1: false, bd3: false, bd2: false, bd4: false });

  const tabs = [
    { id: "resumen", icon: Printer, label: "Resumen" },
    { id: "insumos", icon: Droplet, label: "Insumos" },
    { id: "alertas", icon: AlertCircle, label: "Alertas" },
    { id: "reemplazos", icon: RefreshCw, label: "Reemplazos" },
    { id: "contadores", icon: Hash, label: "Contadores" }
  ];

  const summaryCards = useMemo(() => {
    const resumen = result?.resumen || {};
    const contadores = result?.contadores || {};
    return [
      ["Número de Serie", resumen.numero_serie || resumen.numero_serie_idx || resumen.n_mero_serie || "-"],
      ["Cliente / Cuenta", resumen.nombre_cuenta || contadores?.nombre_cuenta || "-"],
      ["Fabricante", resumen.fabricante || contadores?.fabricante || "-"],
      ["Modelo", resumen.modelo || contadores?.modelo || "-"],
      ["IP", resumen.direccion_ip || contadores?.direcci_n_ip || "-"],
      ["Ubicación", resumen.ubicacion || "-"],
      ["ERP", resumen.id_erp || "-"],
      ["Último Reemplazo", resumen.fecha_de_reemplazo_ultima || "-"],
      ["Insumo Último", resumen.suministro_ultimo || "-"],
      ["Parte OEM Última", resumen.parte_oem_ultima || "-"],
      ["Alertas Totales", `${resumen.alertas_total ?? result?.alertas?.length ?? 0}`],
      ["Última Alerta", resumen.alerta_ultima_fecha || "-"]
    ];
  }, [result]);

  const addLog = (msg) => setLogs((prev) => [`${new Date().toLocaleString()} - ${msg}`, ...prev].slice(0, 30));

  const handleSearch = async () => {
    if (!searchQuery.trim()) return alert("Ingresa un número de serie.");
    setIsSearching(true); setError(""); setResult(null);
    try {
      const response = await fetch(`/api/equipo/${encodeURIComponent(searchQuery.trim())}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "No se encontró el equipo.");
      setResult(data); setActiveTab("resumen"); setCurrentView("query");
    } catch (err) { setError(err.message); } finally { setIsSearching(false); }
  };

  const loadOverview = async () => {
    setError("");
    try {
      const response = await fetch("/api/reports/overview");
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "No se pudo cargar el resumen.");
      setOverview(data); setCurrentView("reports");
    } catch (err) { setError(err.message); }
  };

  const uploadManual = async (kind, file) => {
    if (!file) return;
    setUploading((s) => ({ ...s, [kind]: true }));
    const fd = new FormData();
    fd.append("file", file);
    try {
      const response = await fetch(`/api/import/${kind}`, { method: "POST", body: fd });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Error importando archivo.");
      addLog(`${kind.toUpperCase()} manual: ${JSON.stringify(data)}`);
      alert(`Importación ${kind.toUpperCase()} ok`);
    } catch (err) {
      setError(err.message);
      addLog(`${kind.toUpperCase()} manual error: ${err.message}`);
    } finally {
      setUploading((s) => ({ ...s, [kind]: false }));
    }
  };

  const syncGmail = async (kind) => {
    setUploading((s) => ({ ...s, [kind]: true }));
    try {
      const response = await fetch(`/api/sync/${kind}`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Error en sync Gmail.");
      addLog(`Sync ${kind.toUpperCase()}: ${JSON.stringify(data)}`);
      alert(`Sync ${kind.toUpperCase()} ok`);
    } catch (err) {
      setError(err.message);
      addLog(`Sync ${kind.toUpperCase()} error: ${err.message}`);
    } finally {
      setUploading((s) => ({ ...s, [kind]: false }));
    }
  };

  const renderTable = (rows, preferredColumns = []) => {
    if (!rows || rows.length === 0) return <EmptyState text="Sin datos para mostrar." />;
    const keys = preferredColumns.length ? preferredColumns.filter((k) => rows[0] && Object.prototype.hasOwnProperty.call(rows[0], k)) : Object.keys(rows[0]);
    return (
      <div style={{ overflow: "auto" }}>
        <table style={{ width: "100%", minWidth: "960px", fontSize: "14px" }}>
          <thead><tr style={{ background: "#f8fafc" }}>{keys.map((key) => <th key={key} style={th}>{humanize(key)}</th>)}</tr></thead>
          <tbody>{rows.map((row, idx) => <tr key={idx}>{keys.map((key) => <td key={key} style={td}>{stringify(row[key])}</td>)}</tr>)}</tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "#f8fafc" }}>
      <aside style={{ width: 260, background: "#1e293b", color: "#fff", padding: 20 }}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ color: "#CF142B", fontWeight: 900, fontSize: 40 }}>RICOH</div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 10 }}>TECHNOMA</div>
        </div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 12 }}>PRINTANISTA DB OPS</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button onClick={() => setCurrentView("query")} style={navButton(currentView === "query")}><Search size={18}/>Consultar Equipo</button>
          <button onClick={() => setCurrentView("import")} style={navButton(currentView === "import")}><UploadCloud size={18}/>Importar / Sync</button>
          <button onClick={loadOverview} style={navButton(currentView === "reports")}><LayoutDashboard size={18}/>Reportes Globales</button>
        </div>
      </aside>

      <main style={{ flex: 1, padding: 32 }}>
        <div style={{ maxWidth: 1320, margin: "0 auto" }}>
          {error && <div style={{ background: "#fee2e2", color: "#991b1b", padding: 14, borderRadius: 10, marginBottom: 20 }}>{error}</div>}

          {currentView === "import" && (
            <section style={panel}>
              <h2 style={{ marginTop: 0 }}>Importación V3</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                <Box title="Carga manual BD1 (Contadores Ph1)">
                  <input type="file" accept=".xlsx" onChange={(e) => uploadManual("bd1", e.target.files?.[0])} />
                  <small>Sube TECHNOMA_Dispositivos_Ph1_YYMMDD.xlsx</small>
                </Box>
                <Box title="Carga manual BD3 (GV2)">
                  <input type="file" accept=".xlsx" onChange={(e) => uploadManual("bd3", e.target.files?.[0])} />
                  <small>Sube TECHNOMA_Dispositivos_Dispositivos_Detallado_GV2_YYMMDD.xlsx</small>
                </Box>
                <Box title="Sync Gmail BD2 Alertas">
                  <button style={actionBtn} onClick={() => syncGmail("bd2")} disabled={uploading.bd2}><MailCheck size={16}/> {uploading.bd2 ? "Procesando..." : "Sincronizar BD2"}</button>
                  <small>Requiere secrets/token_technoma.json montado en Docker.</small>
                </Box>
                <Box title="Sync Gmail BD3 Insumos">
                  <button style={actionBtn} onClick={() => syncGmail("bd3")} disabled={uploading.bd3}><MailCheck size={16}/> {uploading.bd3 ? "Procesando..." : "Sincronizar BD3"}</button>
                  <small>Requiere token Gmail y adjuntos GV2.</small>
                </Box>
                <Box title="Sync Gmail BD4 Reemplazos">
                  <button style={actionBtn} onClick={() => syncGmail("bd4")} disabled={uploading.bd4}><MailCheck size={16}/> {uploading.bd4 ? "Procesando..." : "Sincronizar BD4"}</button>
                  <small>Requiere token Gmail y adjuntos de reemplazos.</small>
                </Box>
                <Box title="Logs">
                  <div style={{ maxHeight: 240, overflow: "auto", background: "#0f172a", color: "#e2e8f0", borderRadius: 10, padding: 12 }}>
                    {logs.length ? logs.map((l, i) => <div key={i} style={{ marginBottom: 8 }}>{l}</div>) : "Sin eventos todavía."}
                  </div>
                </Box>
              </div>
            </section>
          )}

          {currentView === "reports" && (
            <section style={panel}>
              <h2 style={{ marginTop: 0 }}>Reportes Globales</h2>
              {!overview ? <EmptyState text="Carga el resumen global."/> : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
                  <MetricCard title="Equipos con alertas" value={overview.equipos_con_alertas ?? "-"} />
                  <MetricCard title="Alertas activas" value={overview.alertas_activas} />
                  <MetricCard title="Reemplazos" value={overview.reemplazos} />
                  <MetricCard title="Equipos en resumen" value={overview.equipos_resumen} />
                </div>
              )}
            </section>
          )}

          {currentView === "query" && (
            <>
              <div style={{ background: "#fff", padding: 20, borderRadius: 14, border: "1px solid #e5e7eb", marginBottom: 24 }}>
                <label style={{ display: "block", marginBottom: 8, fontWeight: 700 }}>Buscar por número de serie</label>
                <div style={{ display: "flex", gap: 12 }}>
                  <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSearch()} placeholder="Ej. 3359P703251" style={{ flex: 1, padding: 12, borderRadius: 10, border: "1px solid #cbd5e1" }} />
                  <button onClick={handleSearch} style={searchBtn}>{isSearching ? "Buscando..." : "Buscar"}</button>
                </div>
              </div>

              {result ? (
                <section style={{ background: "#fff", borderRadius: 14, border: "1px solid #e5e7eb", overflow: "hidden" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", borderBottom: "1px solid #e5e7eb" }}>
                    {tabs.map((tab) => <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={tabStyle(activeTab === tab.id)}><tab.icon size={16}/>{tab.label}</button>)}
                  </div>
                  <div style={{ padding: 24 }}>
                    {activeTab === "resumen" && <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>{summaryCards.map(([label, value]) => <Card key={label} label={label} value={value}/>)}</div>}
                    {activeTab === "insumos" && renderTable(result.insumos, ["suministro","parte_oem","numero_de_serie_del_suministro","fecha_instalacion","fecha_de_reemplazo","contador_al_reemplazo","rendimiento_alcanzado","cobertura_alcanzada","proveedor_de_cartuchos"])}
                    {activeTab === "alertas" && renderTable(result.alertas, ["report_date","nombre_cuenta","fabricante","modelo","numero_serie","n_mero_serie","serial","serie","alerta","descripcion","sourcefile"])}
                    {activeTab === "reemplazos" && renderTable(result.reemplazos, ["report_date","suministro","parte_oem","numero_de_serie_del_suministro","fecha_instalacion","fecha_de_reemplazo","contador_al_reemplazo","nivel_al_reemplazo_pct","rendimiento_alcanzado","cobertura_alcanzada","proveedor_de_cartuchos"])}
                    {activeTab === "contadores" && (result.contadores ? <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>{Object.entries(result.contadores).map(([k,v]) => <Card key={k} label={humanize(k)} value={stringify(v)}/>)}</div> : <EmptyState text="No hay contadores para esta serie."/>)}
                  </div>
                </section>
              ) : (
                <section style={{ background: "#fff", borderRadius: 14, border: "1px solid #e5e7eb", padding: 48, textAlign: "center", color: "#64748b" }}>
                  <ServerCrash size={48} style={{ marginBottom: 12 }} />
                  Ingresa una serie para consultar el equipo.
                </section>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

const panel = { background: "#fff", borderRadius: 14, border: "1px solid #e5e7eb", padding: 24 };
const th = { textAlign: "left", padding: "12px", borderBottom: "1px solid #e5e7eb", whiteSpace: "nowrap" };
const td = { padding: "12px", borderBottom: "1px solid #f1f5f9", verticalAlign: "top" };
const actionBtn = { background: "#111827", color: "#fff", border: "none", padding: "10px 14px", borderRadius: 10, fontWeight: 700, display: "inline-flex", gap: 8, alignItems: "center" };
const searchBtn = { background: "#111827", color: "#fff", border: "none", padding: "12px 18px", borderRadius: 10, fontWeight: 700 };
function humanize(value){return String(value).replaceAll("_"," ").replace(/\s+/g," ").trim().replace(/\b\w/g,(c)=>c.toUpperCase())}
function stringify(value){if(value===null||value===undefined||value==="")return "-";return String(value)}
function navButton(active){return{display:"flex",alignItems:"center",gap:10,width:"100%",padding:"12px 14px",borderRadius:10,border:"none",background:active?"#ef4444":"transparent",color:"#fff",fontWeight:active?700:500,textAlign:"left",cursor:"pointer"}}
function tabStyle(active){return{display:"flex",alignItems:"center",gap:8,padding:"14px 18px",border:"none",background:active?"#fef2f2":"#fff",color:active?"#dc2626":"#475569",fontWeight:600,borderBottom:active?"2px solid #ef4444":"2px solid transparent",cursor:"pointer"}}
function Card({label,value}){return <div style={{background:"#f8fafc",border:"1px solid #e5e7eb",borderRadius:12,padding:16}}><div style={{fontSize:12,color:"#64748b",marginBottom:6}}>{label}</div><div style={{fontWeight:700,wordBreak:"break-word"}}>{value}</div></div>}
function MetricCard({title,value}){return <div style={{background:"#eff6ff",border:"1px solid #bfdbfe",borderRadius:12,padding:18}}><div style={{fontWeight:600,marginBottom:8}}>{title}</div><div style={{fontSize:28,fontWeight:800}}>{value}</div></div>}
function EmptyState({text}){return <div style={{color:"#64748b",padding:20}}>{text}</div>}
function Box({title, children}){return <div style={{border:"1px solid #e5e7eb",borderRadius:12,padding:16,display:"flex",flexDirection:"column",gap:10}}><div style={{fontWeight:700}}>{title}</div>{children}</div>}
