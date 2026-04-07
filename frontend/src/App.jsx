\
import React, { useEffect, useMemo, useState } from "react";
import { LayoutDashboard, UploadCloud, History, Search, RefreshCw, MailCheck } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line } from "recharts";

const styles = {
  shell: { minHeight: "100vh", display: "flex" },
  aside: { width: 280, background: "linear-gradient(180deg, #111827, #1f2937)", color: "#fff", padding: 22, display: "flex", flexDirection: "column" },
  main: { flex: 1, padding: 28, background: "#f6f8fb" },
  card: { background: "#fff", border: "1px solid #e5e7eb", borderRadius: 18, padding: 18, boxShadow: "0 10px 30px rgba(15,23,42,0.04)" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 },
  btn: { background: "#dc2626", color: "#fff", border: "none", borderRadius: 12, padding: "12px 18px", fontWeight: 700, cursor: "pointer" },
  ghost: { background: "#fff", color: "#0f172a", border: "1px solid #e5e7eb", borderRadius: 12, padding: "10px 14px", fontWeight: 700, cursor: "pointer" },
  nav: (active) => ({ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "13px 14px", borderRadius: 12, border: "1px solid transparent", background: active ? "rgba(220,38,38,0.18)" : "transparent", color: "#fff", fontWeight: 700, cursor: "pointer", textAlign: "left" }),
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14 },
  th: { textAlign: "left", padding: 12, borderBottom: "1px solid #e5e7eb", background: "#f8fafc" },
  td: { padding: 12, borderBottom: "1px solid #f1f5f9" },
};

function humanize(v) {
  return String(v || "").replaceAll("_", " ").replace(/\s+/g, " ").trim().replace(/\b\w/g, c => c.toUpperCase());
}
function fmt(v) {
  if (v === null || v === undefined || v === "") return "-";
  return Number.isFinite(Number(v)) ? new Intl.NumberFormat("es-ES").format(Number(v)) : String(v);
}

export default function App() {
  const [view, setView] = useState("dashboard");
  const [dashboard, setDashboard] = useState({ kpis: {}, clientes: [], timeline: [] });
  const [jobs, setJobs] = useState([]);
  const [detail, setDetail] = useState([]);
  const [detailTitle, setDetailTitle] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [serie, setSerie] = useState("");
  const [equipo, setEquipo] = useState(null);

  const query = useMemo(() => {
    const qs = new URLSearchParams();
    if (dateFrom) qs.set("date_from", dateFrom);
    if (dateTo) qs.set("date_to", dateTo);
    const s = qs.toString();
    return s ? `?${s}` : "";
  }, [dateFrom, dateTo]);

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const raw = await response.text();
    let data;
    try { data = JSON.parse(raw); }
    catch { throw new Error(raw || `Error HTTP ${response.status}`); }
    if (!response.ok) throw new Error(data.detail || "Error de API");
    return data;
  }

  async function loadDashboard() {
    setError("");
    try {
      const [summary, jobsData] = await Promise.all([
        fetchJson(`/api/dashboard/summary${query}`),
        fetchJson(`/api/jobs`)
      ]);
      setDashboard(summary);
      setJobs(jobsData);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { loadDashboard(); }, [query]);

  async function uploadFile(kind, file) {
    if (!file) return;
    setError(""); setMessage("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const data = await fetchJson(`/api/import/${kind}`, { method: "POST", body: fd });
      setMessage(JSON.stringify(data, null, 2));
      await loadDashboard();
      setView("import");
    } catch (e) { setError(e.message); }
  }

  async function runSync(kind) {
    setError(""); setMessage("");
    try {
      const data = await fetchJson(`/api/sync/${kind}`, { method: "POST" });
      setMessage(JSON.stringify(data, null, 2));
      await loadDashboard();
      setView("import");
    } catch (e) { setError(e.message); }
  }

  async function loadClientDetail(cliente) {
    try {
      const data = await fetchJson(`/api/detail/alertas?cliente=${encodeURIComponent(cliente)}${query ? "&" + query.slice(1) : ""}`);
      setDetail(data);
      setDetailTitle(`Detalle de alertas: ${cliente}`);
      setView("detalle");
    } catch (e) { setError(e.message); }
  }

  async function buscarEquipo() {
    if (!serie.trim()) return;
    setError("");
    try {
      const data = await fetchJson(`/api/equipo/${encodeURIComponent(serie.trim())}`);
      setEquipo(data);
      setView("equipo");
    } catch (e) { setError(e.message); }
  }

  const renderTable = (rows) => {
    if (!rows || rows.length === 0) return <div style={{ color: "#64748b" }}>Sin datos.</div>;
    const cols = Object.keys(rows[0]);
    return (
      <div style={{ overflow: "auto" }}>
        <table style={styles.table}>
          <thead><tr>{cols.map(c => <th key={c} style={styles.th}>{humanize(c)}</th>)}</tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {cols.map(c => <td key={c} style={styles.td}>{String(r[c] ?? "-")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={styles.shell}>
      <aside style={styles.aside}>
        <div style={{ marginBottom: 28 }}>
          <div style={{ color: "#dc2626", fontWeight: 900, fontSize: 42, letterSpacing: -1.6 }}>RICOH</div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 6 }}>TECHNOMA</div>
        </div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 14, letterSpacing: 0.8 }}>PRINTANISTA DB OPS</div>

        <button style={styles.nav(view === "dashboard")} onClick={() => setView("dashboard")}><LayoutDashboard size={18}/>Dashboard</button>
        <button style={styles.nav(view === "import")} onClick={() => setView("import")}><UploadCloud size={18}/>Importar / Sync</button>
        <button style={styles.nav(view === "history")} onClick={() => setView("history")}><History size={18}/>Historial</button>
        <button style={styles.nav(view === "busqueda")} onClick={() => setView("busqueda")}><Search size={18}/>Consultar Equipo</button>
      </aside>

      <main style={styles.main}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <div>
            <div style={{ fontSize: 30, fontWeight: 800, color: "#0f172a" }}>
              {view === "dashboard" && "Dashboard Ejecutivo"}
              {view === "import" && "Panel de Importación"}
              {view === "history" && "Historial de Jobs"}
              {view === "detalle" && detailTitle}
              {view === "busqueda" && "Consulta por Número de Serie"}
              {view === "equipo" && "Detalle del Equipo"}
            </div>
            <div style={{ color: "#64748b", marginTop: 6 }}>
              {view === "dashboard" && "KPIs, gráficos, línea de tiempo y detalle por cliente."}
              {view === "import" && "Carga manual y Gmail con trazabilidad."}
              {view === "history" && "Seguimiento de ejecuciones e importaciones."}
            </div>
          </div>
          <button style={styles.ghost} onClick={loadDashboard}><RefreshCw size={16} style={{verticalAlign:"middle", marginRight:8}}/>Refrescar</button>
        </div>

        {error && <div style={{ ...styles.card, background: "#fee2e2", color: "#991b1b", marginBottom: 16 }}>{error}</div>}

        {(view === "dashboard" || view === "detalle") && (
          <div style={{ ...styles.card, marginBottom: 18, display: "flex", gap: 10, alignItems: "end", flexWrap: "wrap" }}>
            <div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>Desde</div><input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} /></div>
            <div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>Hasta</div><input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} /></div>
            <button style={styles.btn} onClick={loadDashboard}>Aplicar filtros</button>
          </div>
        )}

        {view === "dashboard" && (
          <>
            <section style={{ ...styles.grid, marginBottom: 18 }}>
              <div style={styles.card}><div style={{ color: "#64748b", fontSize: 13, fontWeight: 600 }}>Equipos monitoreados</div><div style={{ fontSize: 30, fontWeight: 800, marginTop: 8 }}>{fmt(dashboard.kpis.equipos_monitoreados)}</div></div>
              <div style={styles.card}><div style={{ color: "#64748b", fontSize: 13, fontWeight: 600 }}>Alertas activas</div><div style={{ fontSize: 30, fontWeight: 800, marginTop: 8 }}>{fmt(dashboard.kpis.alertas_activas)}</div></div>
              <div style={styles.card}><div style={{ color: "#64748b", fontSize: 13, fontWeight: 600 }}>Reemplazos</div><div style={{ fontSize: 30, fontWeight: 800, marginTop: 8 }}>{fmt(dashboard.kpis.reemplazos)}</div></div>
              <div style={styles.card}><div style={{ color: "#64748b", fontSize: 13, fontWeight: 600 }}>% equipos con alertas</div><div style={{ fontSize: 30, fontWeight: 800, marginTop: 8 }}>{fmt(dashboard.kpis.porc_equipos_con_alertas)}%</div></div>
            </section>

            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div style={styles.card}>
                <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 14 }}>Alertas por Cliente</div>
                <div style={{ width: "100%", height: 320 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dashboard.clientes} onClick={(e) => { if (e?.activeLabel) loadClientDetail(e.activeLabel); }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" hide />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="total" fill="#dc2626" radius={[6,6,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ color: "#64748b", fontSize: 12 }}>Haz click en una barra para abrir el detalle.</div>
              </div>
              <div style={styles.card}>
                <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 14 }}>Línea de Tiempo de Alertas</div>
                <div style={{ width: "100%", height: 320 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dashboard.timeline}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="total" stroke="#0f172a" strokeWidth={2.5} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>
          </>
        )}

        {view === "import" && (
          <>
            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 18 }}>
              <div style={styles.card}>
                <div style={{ fontWeight: 800, marginBottom: 8 }}>Importar BD1</div>
                <div style={{ color: "#64748b", fontSize: 13, marginBottom: 12 }}>Sube un archivo y registra el job.</div>
                <input type="file" accept=".xlsx,.csv" onChange={e => uploadFile("bd1", e.target.files?.[0])}/>
              </div>
              <div style={styles.card}>
                <div style={{ fontWeight: 800, marginBottom: 8 }}>Importar BD3</div>
                <div style={{ color: "#64748b", fontSize: 13, marginBottom: 12 }}>Sube un archivo y registra el job.</div>
                <input type="file" accept=".xlsx,.csv" onChange={e => uploadFile("bd3", e.target.files?.[0])}/>
              </div>
            </section>

            <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 18 }}>
              <div style={styles.card}>
                <div style={{ fontWeight: 800, marginBottom: 12 }}>Gmail Sync</div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <button style={styles.btn} onClick={() => runSync("bd2")}><MailCheck size={16} style={{marginRight:8, verticalAlign:"middle"}}/>Sync BD2</button>
                  <button style={styles.btn} onClick={() => runSync("bd3")}><MailCheck size={16} style={{marginRight:8, verticalAlign:"middle"}}/>Sync BD3</button>
                  <button style={styles.btn} onClick={() => runSync("bd4")}><MailCheck size={16} style={{marginRight:8, verticalAlign:"middle"}}/>Sync BD4</button>
                  <button style={styles.btn} onClick={() => runSync("all")}><MailCheck size={16} style={{marginRight:8, verticalAlign:"middle"}}/>Sync All</button>
                </div>
                <div style={{ color: "#64748b", fontSize: 12, marginTop: 10 }}>Requiere `secrets/token_technoma.json` montado en `/app/secrets`.</div>
              </div>
              <div style={styles.card}>
                <div style={{ fontWeight: 800, marginBottom: 8 }}>Resultado de la última ejecución</div>
                <pre style={{ margin: 0, background: "#0f172a", color: "#e2e8f0", padding: 16, borderRadius: 12, minHeight: 160 }}>{message || "Todavía no hay resultados."}</pre>
              </div>
            </section>
          </>
        )}

        {view === "history" && <section style={styles.card}>{renderTable(jobs)}</section>}
        {view === "detalle" && <section style={styles.card}>{renderTable(detail)}</section>}

        {view === "busqueda" && (
          <section style={styles.card}>
            <div style={{ marginBottom: 12, fontWeight: 800 }}>Buscar serie</div>
            <div style={{ display: "flex", gap: 10 }}>
              <input value={serie} onChange={e => setSerie(e.target.value)} placeholder="Ej. 3359P703251" style={{ flex: 1, padding: 12, borderRadius: 12, border: "1px solid #cbd5e1" }}/>
              <button style={styles.btn} onClick={buscarEquipo}>Buscar</button>
            </div>
          </section>
        )}

        {view === "equipo" && <section style={styles.card}>{renderTable(equipo ? [equipo] : [])}</section>}
      </main>
    </div>
  );
}
