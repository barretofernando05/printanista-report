
import React, { useEffect, useMemo, useState } from "react";
import { Search, Printer, Droplet, AlertCircle, RefreshCw, Hash, ServerCrash, UploadCloud, MailCheck, DatabaseZap, BarChart3, History, CheckCircle2 } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line, PieChart, Pie, Cell } from "recharts";
const PIE = ["#dc2626","#f97316","#eab308","#22c55e","#3b82f6","#8b5cf6","#ec4899","#06b6d4"];

export default function App(){
  const [view,setView]=useState("dashboard");
  const [activeTab,setActiveTab]=useState("resumen");
  const [searchQuery,setSearchQuery]=useState("");
  const [isSearching,setIsSearching]=useState(false);
  const [result,setResult]=useState(null);
  const [overview,setOverview]=useState(null);
  const [dashboard,setDashboard]=useState({kpis:null,alertasCliente:[],alertasFabricante:[],reemplazosMes:[],topMono:[],topColor:[],equiposFabricante:[]});
  const [jobs,setJobs]=useState([]);
  const [lastResult,setLastResult]=useState(null);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState({bd1:false,bd3:false,bd2:false,bd4:false,syncall:false,dashboard:false});

  const tabs=[{id:"resumen",icon:Printer,label:"Resumen"},{id:"insumos",icon:Droplet,label:"Insumos"},{id:"alertas",icon:AlertCircle,label:"Alertas"},{id:"reemplazos",icon:RefreshCw,label:"Reemplazos"},{id:"contadores",icon:Hash,label:"Contadores"}];

  const summaryCards=useMemo(()=>{const r=result?.resumen||{}; const c=result?.contadores||{}; return [["Número de Serie",r.numero_serie||r.numero_serie_idx||r.n_mero_serie||"-"],["Cliente / Cuenta",r.nombre_cuenta||c?.nombre_cuenta||"-"],["Fabricante",r.fabricante||c?.fabricante||"-"],["Modelo",r.modelo||c?.modelo||"-"],["IP",r.direccion_ip||c?.direcci_n_ip||"-"],["Ubicación",r.ubicacion||"-"],["ERP",r.id_erp||"-"],["Último Reemplazo",r.fecha_de_reemplazo_ultima||"-"],["Insumo Último",r.suministro_ultimo||"-"],["Parte OEM Última",r.parte_oem_ultima||"-"],["Alertas Totales",`${r.alertas_total??result?.alertas?.length??0}`],["Última Alerta",r.alerta_ultima_fecha||"-"]]},[result]);

  const fetchJson=async(url,options={})=>{const response=await fetch(url,options); const data=await response.json(); if(!response.ok) throw new Error(data.detail||"Error de API."); return data;};

  const loadDashboard=async()=>{setBusy(s=>({...s,dashboard:true})); setError(""); try{
    const [kpis,overviewData,alertasCliente,alertasFabricante,reemplazosMes,topMono,topColor,equiposFabricante,jobsData]=await Promise.all([
      fetchJson("/api/dashboard/kpis"),fetchJson("/api/reports/overview"),fetchJson("/api/dashboard/alertas-por-cliente"),fetchJson("/api/dashboard/alertas-por-fabricante"),
      fetchJson("/api/dashboard/reemplazos-por-mes"),fetchJson("/api/dashboard/top-mono"),fetchJson("/api/dashboard/top-color"),fetchJson("/api/dashboard/equipos-por-fabricante"),fetchJson("/api/jobs?limit=25")
    ]);
    setDashboard({kpis,alertasCliente,alertasFabricante,reemplazosMes,topMono,topColor,equiposFabricante}); setOverview(overviewData); setJobs(jobsData);
  }catch(err){setError(err.message)} finally {setBusy(s=>({...s,dashboard:false}))}};
  useEffect(()=>{loadDashboard()},[]);

  const handleSearch=async()=>{if(!searchQuery.trim()) return alert("Ingresa un número de serie."); setIsSearching(true); setError(""); setResult(null); try{const data=await fetchJson(`/api/equipo/${encodeURIComponent(searchQuery.trim())}`); setResult(data); setActiveTab("resumen"); setView("query")}catch(err){setError(err.message)} finally {setIsSearching(false)}};
  const uploadManual=async(kind,file)=>{if(!file)return; setBusy(s=>({...s,[kind]:true})); const fd=new FormData(); fd.append("file",file); try{const data=await fetchJson(`/api/import/${kind}`,{method:"POST",body:fd}); setLastResult(data); await loadDashboard(); alert(`Importación ${kind.toUpperCase()} ok`)}catch(err){setError(err.message)} finally {setBusy(s=>({...s,[kind]:false}))}};
  const syncGmail=async(kind)=>{setBusy(s=>({...s,[kind]:true})); try{const data=await fetchJson(`/api/sync/${kind}`,{method:"POST"}); setLastResult(data); await loadDashboard(); alert(`Sync ${kind.toUpperCase()} ok`)}catch(err){setError(err.message)} finally {setBusy(s=>({...s,[kind]:false}))}};
  const syncAll=async()=>{setBusy(s=>({...s,syncall:true})); try{const data=await fetchJson(`/api/sync/all`,{method:"POST"}); setLastResult(data); await loadDashboard(); alert("Sync ALL ok")}catch(err){setError(err.message)} finally {setBusy(s=>({...s,syncall:false}))}};

  const renderTable=(rows,preferredColumns=[])=>{if(!rows||rows.length===0) return <EmptyState text="Sin datos para mostrar."/>; const keys=preferredColumns.length?preferredColumns.filter(k=>rows[0]&&Object.prototype.hasOwnProperty.call(rows[0],k)):Object.keys(rows[0]); return <div style={{overflow:"auto"}}><table style={{width:"100%",minWidth:"960px",fontSize:"14px"}}><thead><tr style={{background:"#f8fafc"}}>{keys.map(key=><th key={key} style={styles.th}>{humanize(key)}</th>)}</tr></thead><tbody>{rows.map((row,idx)=><tr key={idx}>{keys.map(key=><td key={key} style={styles.td}>{stringify(row[key])}</td>)}</tr>)}</tbody></table></div>};

  return <div style={styles.shell}>
    <aside style={styles.aside}>
      <div style={{marginBottom:28}}><div style={styles.brand}>RICOH</div><div style={styles.subbrand}>TECHNOMA</div></div>
      <div style={styles.caption}>PRINTANISTA DB OPS</div>
      <div style={{display:"flex",flexDirection:"column",gap:10}}>
        <NavButton active={view==="dashboard"} icon={BarChart3} onClick={()=>setView("dashboard")}>Dashboard</NavButton>
        <NavButton active={view==="query"} icon={Search} onClick={()=>setView("query")}>Consultar Equipo</NavButton>
        <NavButton active={view==="import"} icon={UploadCloud} onClick={()=>setView("import")}>Importar / Sync</NavButton>
        <NavButton active={view==="history"} icon={History} onClick={()=>setView("history")}>Historial</NavButton>
      </div>
    </aside>
    <main style={styles.main}>
      <div style={styles.header}>
        <div><div style={styles.pageTitle}>{view==="dashboard"?"Dashboard Ejecutivo":view==="query"?"Consulta por Equipo":view==="import"?"Importación y Sincronización":"Historial de Ejecuciones"}</div><div style={styles.pageSubtitle}>{view==="dashboard"?"KPIs, gráficos, tendencias y métricas globales.":view==="query"?"Consulta operacional por serie con detalle técnico.":view==="import"?"Carga manual y sincronización automática con trazabilidad.":"Resultado detallado de cada job y sincronización."}</div></div>
        <div style={styles.headerRight}><button style={styles.ghostBtn} onClick={loadDashboard} disabled={busy.dashboard}><DatabaseZap size={16}/>{busy.dashboard?"Actualizando...":"Refrescar"}</button></div>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {view==="dashboard" && <>
        <section style={styles.metricsGrid}>
          <MetricCard title="Equipos monitoreados" value={fmt(dashboard.kpis?.equipos_monitoreados)}/>
          <MetricCard title="Alertas activas" value={fmt(dashboard.kpis?.alertas_activas)}/>
          <MetricCard title="Reemplazos" value={fmt(dashboard.kpis?.reemplazos)}/>
          <MetricCard title="Páginas mono" value={fmt(dashboard.kpis?.paginas_mono)}/>
          <MetricCard title="Páginas color" value={fmt(dashboard.kpis?.paginas_color)}/>
          <MetricCard title="% equipos con alertas" value={`${fmt(dashboard.kpis?.porc_equipos_con_alertas)}%`}/>
        </section>
        <section style={styles.chartGrid2}>
          <Panel title="Alertas por Cliente"><ChartWrap><ResponsiveContainer width="100%" height="100%"><BarChart data={dashboard.alertasCliente}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name" hide/><YAxis/><Tooltip/><Bar dataKey="total" fill="#dc2626" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></ChartWrap></Panel>
          <Panel title="Alertas por Fabricante"><ChartWrap><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={dashboard.alertasFabricante} dataKey="total" nameKey="name" outerRadius={95} innerRadius={45}>{dashboard.alertasFabricante.map((_,idx)=><Cell key={idx} fill={PIE[idx%PIE.length]}/>)}</Pie><Tooltip/><Legend/></PieChart></ResponsiveContainer></ChartWrap></Panel>
        </section>
        <section style={styles.chartGrid2}>
          <Panel title="Reemplazos por Mes"><ChartWrap><ResponsiveContainer width="100%" height="100%"><LineChart data={[...dashboard.reemplazosMes].reverse()}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis/><Tooltip/><Line type="monotone" dataKey="total" stroke="#0f172a" strokeWidth={2.5} dot={{r:3}}/></LineChart></ResponsiveContainer></ChartWrap></Panel>
          <Panel title="Equipos por Fabricante"><ChartWrap><ResponsiveContainer width="100%" height="100%"><BarChart data={dashboard.equiposFabricante}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name" hide/><YAxis/><Tooltip/><Bar dataKey="total" fill="#3b82f6" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></ChartWrap></Panel>
        </section>
      </>}

      {view==="query" && <>
        <section style={styles.searchPanel}><label style={styles.searchLabel}>Buscar por número de serie</label><div style={styles.searchRow}><input value={searchQuery} onChange={e=>setSearchQuery(e.target.value)} onKeyDown={e=>e.key==="Enter"&&handleSearch()} placeholder="Ej. 3359P703251" style={styles.searchInput}/><button onClick={handleSearch} style={styles.primaryBtn}>{isSearching?"Buscando...":"Buscar"}</button></div></section>
        {result ? <section style={styles.panel}><div style={styles.tabsRow}>{tabs.map(tab=><TabButton key={tab.id} active={activeTab===tab.id} icon={tab.icon} onClick={()=>setActiveTab(tab.id)}>{tab.label}</TabButton>)}</div><div style={{padding:24}}>
          {activeTab==="resumen" && <div style={styles.metricsGrid}>{summaryCards.map(([label,value])=><InfoCard key={label} label={label} value={value}/>)}</div>}
          {activeTab==="insumos" && renderTable(result.insumos,["suministro","parte_oem","numero_de_serie_del_suministro","fecha_instalacion","fecha_de_reemplazo","contador_al_reemplazo","rendimiento_alcanzado","cobertura_alcanzada","proveedor_de_cartuchos"])}
          {activeTab==="alertas" && renderTable(result.alertas,["report_date","nombre_cuenta","fabricante","modelo","numero_serie","n_mero_serie","serial","serie","alerta","descripcion","sourcefile"])}
          {activeTab==="reemplazos" && renderTable(result.reemplazos,["report_date","suministro","parte_oem","numero_de_serie_del_suministro","fecha_instalacion","fecha_de_reemplazo","contador_al_reemplazo","nivel_al_reemplazo_pct","rendimiento_alcanzado","cobertura_alcanzada","proveedor_de_cartuchos"])}
          {activeTab==="contadores" && (result.contadores ? <div style={styles.metricsGrid}>{Object.entries(result.contadores).map(([k,v])=><InfoCard key={k} label={humanize(k)} value={stringify(v)}/>)}</div> : <EmptyState text="No hay contadores para esta serie."/>)}
        </div></section> : <section style={styles.emptyPanel}><ServerCrash size={48} style={{marginBottom:12}}/>Ingresa una serie para consultar el equipo.</section>}
      </>}

      {view==="import" && <>
        <section style={styles.importGrid}>
          <ImportCard title="Carga manual BD1" subtitle="Contadores Ph1" helper="Sube TECHNOMA_Dispositivos_Ph1_YYMMDD.xlsx" input={<input type="file" accept=".xlsx" onChange={e=>uploadManual("bd1",e.target.files?.[0])}/>}/>
          <ImportCard title="Carga manual BD3" subtitle="Dispositivos Detallado GV2" helper="Sube TECHNOMA_Dispositivos_Dispositivos_Detallado_GV2_YYMMDD.xlsx" input={<input type="file" accept=".xlsx" onChange={e=>uploadManual("bd3",e.target.files?.[0])}/>}/>
          <ImportCard title="Sync Gmail BD2" subtitle="Alertas" helper="Usa token_technoma.json montado en /app/secrets" input={<button style={styles.primaryBtn} onClick={()=>syncGmail("bd2")} disabled={busy.bd2}><MailCheck size={16}/> {busy.bd2?"Procesando...":"Sincronizar BD2"}</button>}/>
          <ImportCard title="Sync Gmail BD3" subtitle="Insumos / GV2" helper="Procesa adjuntos GV2 del correo" input={<button style={styles.primaryBtn} onClick={()=>syncGmail("bd3")} disabled={busy.bd3}><MailCheck size={16}/> {busy.bd3?"Procesando...":"Sincronizar BD3"}</button>}/>
          <ImportCard title="Sync Gmail BD4" subtitle="Reemplazos" helper="Procesa adjuntos de reemplazos" input={<button style={styles.primaryBtn} onClick={()=>syncGmail("bd4")} disabled={busy.bd4}><MailCheck size={16}/> {busy.bd4?"Procesando...":"Sincronizar BD4"}</button>}/>
          <ImportCard title="Sync Automático / Global" subtitle="Ejecución combinada" helper="También corre por scheduler si AUTO_SYNC_ENABLED=true" input={<button style={styles.primaryBtn} onClick={syncAll} disabled={busy.syncall}><RefreshCw size={16}/> {busy.syncall?"Procesando...":"Sincronizar Todo"}</button>}/>
        </section>
        {lastResult && <section style={{...styles.panel,marginTop:18,padding:20}}><div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14,fontWeight:800}}><CheckCircle2 size={18} color="#16a34a"/> Resultado de la última carga</div><div style={styles.metricsGrid}>
          <InfoCard label="Estado" value={lastResult.status||"-"}/><InfoCard label="Tabla destino" value={lastResult.target_table||"-"}/><InfoCard label="Archivo" value={lastResult.source_name||"-"}/><InfoCard label="Fecha detectada" value={lastResult.reportdate||"-"}/><InfoCard label="Insertadas" value={fmt(lastResult.rows_inserted)}/><InfoCard label="Actualizadas" value={fmt(lastResult.rows_updated)}/><InfoCard label="Omitidas" value={fmt(lastResult.rows_ignored)}/><InfoCard label="Archivos procesados" value={fmt(lastResult.files_processed)}/>
        </div></section>}
      </>}

      {view==="history" && <section style={styles.panel}><div style={{padding:20,borderBottom:"1px solid #e5e7eb",display:"flex",alignItems:"center",gap:10,fontWeight:800}}><History size={18}/> Historial de Jobs</div><div style={{padding:20}}>{renderTable(jobs,["id","job_name","source_type","source_name","status","started_at","finished_at","files_processed","files_skipped","rows_inserted","rows_updated","rows_ignored","error_text"])}</div></section>}
    </main>
  </div>;
}

const styles={shell:{minHeight:"100vh",display:"flex",background:"var(--bg)"},aside:{width:280,background:"linear-gradient(180deg, var(--nav), var(--nav2))",color:"#fff",padding:22,display:"flex",flexDirection:"column"},brand:{color:"var(--brand)",fontWeight:900,fontSize:42,letterSpacing:-1.6},subbrand:{fontSize:22,fontWeight:700,marginTop:6},caption:{fontSize:12,color:"#94a3b8",marginBottom:14,letterSpacing:0.8},main:{flex:1,padding:28},header:{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24},pageTitle:{fontSize:30,fontWeight:800,color:"#0f172a"},pageSubtitle:{color:"#64748b",marginTop:6},headerRight:{display:"flex",gap:12},ghostBtn:{display:"inline-flex",gap:8,alignItems:"center",background:"#fff",border:"1px solid #e5e7eb",color:"#0f172a",borderRadius:12,padding:"10px 14px",fontWeight:700,boxShadow:"0 1px 2px rgba(0,0,0,0.04)"},error:{background:"#fee2e2",color:"#991b1b",padding:14,borderRadius:12,marginBottom:20,border:"1px solid #fecaca"},panel:{background:"#fff",borderRadius:18,border:"1px solid #e5e7eb",overflow:"hidden",boxShadow:"0 10px 30px rgba(15,23,42,0.04)"},searchPanel:{background:"#fff",padding:22,borderRadius:18,border:"1px solid #e5e7eb",marginBottom:24,boxShadow:"0 10px 30px rgba(15,23,42,0.04)"},searchLabel:{display:"block",marginBottom:10,fontWeight:700},searchRow:{display:"flex",gap:12},searchInput:{flex:1,padding:14,borderRadius:12,border:"1px solid #cbd5e1",outline:"none",background:"#fff"},primaryBtn:{background:"var(--brand)",color:"#fff",border:"none",padding:"12px 18px",borderRadius:12,fontWeight:700,display:"inline-flex",alignItems:"center",gap:8,boxShadow:"0 10px 20px rgba(220,38,38,0.15)"},metricsGrid:{display:"grid",gridTemplateColumns:"repeat(auto-fit, minmax(210px, 1fr))",gap:16,marginBottom:24},chartGrid2:{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:24},importGrid:{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16},emptyPanel:{background:"#fff",borderRadius:18,border:"1px solid #e5e7eb",padding:60,textAlign:"center",color:"#64748b",boxShadow:"0 10px 30px rgba(15,23,42,0.04)"},tabsRow:{display:"flex",flexWrap:"wrap",borderBottom:"1px solid #e5e7eb"},th:{textAlign:"left",padding:"12px",borderBottom:"1px solid #e5e7eb",whiteSpace:"nowrap",fontWeight:700,color:"#334155"},td:{padding:"12px",borderBottom:"1px solid #f1f5f9",verticalAlign:"top",color:"#0f172a"}};
function fmt(v){if(v===null||v===undefined||v==="")return "-";return Number.isFinite(Number(v))?new Intl.NumberFormat("es-ES").format(Number(v)):String(v)}
function humanize(v){return String(v).replaceAll("_"," ").replace(/\s+/g," ").trim().replace(/\b\w/g,c=>c.toUpperCase())}
function stringify(v){if(v===null||v===undefined||v==="")return "-";return String(v)}
function NavButton({active,icon:Icon,children,onClick}){return <button onClick={onClick} style={{display:"flex",alignItems:"center",gap:10,width:"100%",padding:"13px 14px",borderRadius:12,border:"1px solid transparent",background:active?"rgba(220,38,38,0.18)":"transparent",color:"#fff",fontWeight:700,textAlign:"left",cursor:"pointer"}}><Icon size={18}/>{children}</button>}
function TabButton({active,icon:Icon,children,onClick}){return <button onClick={onClick} style={{display:"flex",alignItems:"center",gap:8,padding:"14px 18px",border:"none",background:active?"var(--soft)":"#fff",color:active?"var(--brand)":"#475569",fontWeight:700,borderBottom:active?"2px solid var(--brand)":"2px solid transparent",cursor:"pointer"}}><Icon size={16}/>{children}</button>}
function MetricCard({title,value}){return <div style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:18,padding:18,boxShadow:"0 10px 30px rgba(15,23,42,0.04)"}}><div style={{color:"#64748b",fontSize:13,fontWeight:600}}>{title}</div><div style={{fontSize:30,fontWeight:800,marginTop:8}}>{value}</div></div>}
function InfoCard({label,value}){return <div style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:16,padding:16,boxShadow:"0 8px 22px rgba(15,23,42,0.03)"}}><div style={{fontSize:12,color:"#64748b",marginBottom:6,fontWeight:600}}>{label}</div><div style={{fontWeight:800,wordBreak:"break-word"}}>{value}</div></div>}
function Panel({title,children}){return <section style={{background:"#fff",borderRadius:18,border:"1px solid #e5e7eb",padding:18,boxShadow:"0 10px 30px rgba(15,23,42,0.04)"}}><div style={{fontWeight:800,fontSize:16,marginBottom:14}}>{title}</div>{children}</section>}
function ChartWrap({children}){return <div style={{width:"100%",height:320}}>{children}</div>}
function EmptyState({text}){return <div style={{color:"#64748b",padding:20}}>{text}</div>}
function ImportCard({title,subtitle,helper,input}){return <div style={{background:"#fff",borderRadius:18,border:"1px solid #e5e7eb",padding:18,boxShadow:"0 10px 30px rgba(15,23,42,0.04)",display:"flex",flexDirection:"column",gap:12}}><div><div style={{fontWeight:800}}>{title}</div><div style={{color:"#64748b",marginTop:4}}>{subtitle}</div></div>{input}<div style={{fontSize:12,color:"#64748b"}}>{helper}</div></div>}
