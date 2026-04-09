import React, { useEffect, useMemo, useState } from "react";
import { fetchJson } from "../api";
import DateField from "../components/DateField";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";

export default function InicioPage({ openPage, setSerie }) {
  const [data, setData] = useState(null);
  const [serieInput, setSerieInput] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const load = async (from = dateFrom, to = dateTo) => {
    const qs = new URLSearchParams();
    if (from) qs.set("date_from", from);
    if (to) qs.set("date_to", to);

    const url = qs.toString()
      ? `/api/dashboard/home?${qs.toString()}`
      : "/api/dashboard/home";

    const result = await fetchJson(url);
    setData(result);
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const evolucion = useMemo(
    () =>
      (data?.charts?.evolucion_diaria || []).map((r) => ({
        fecha: shortDate(r.fecha),
        total: Number(r.total || 0),
      })),
    [data]
  );

  const alertasDiarias = useMemo(
    () =>
      (data?.charts?.alertas_diarias || []).map((r) => ({
        fecha: shortDate(r.fecha),
        total: Number(r.total || 0),
      })),
    [data]
  );

  const alertasPorTipo = useMemo(() => {
    const rows = data?.charts?.alertas_por_tipo_diaria || [];
    const map = new Map();

    rows.forEach((r) => {
      const fecha = shortDate(r.fecha);
      const tipo = normalizeTipo(r.tipo);
      const total = Number(r.total || 0);

      if (!map.has(fecha)) {
        map.set(fecha, {
          fecha,
          suministro: 0,
          mantenimiento: 0,
          error: 0,
          otros: 0,
        });
      }

      const row = map.get(fecha);
      row[tipo] += total;
    });

    return Array.from(map.values());
  }, [data]);

  const applyQuickRange = (days) => {
    const today = new Date();
    const end = formatDate(today);
    const startDate = new Date();
    startDate.setDate(today.getDate() - days);
    const start = formatDate(startDate);

    setDateFrom(start);
    setDateTo(end);
    load(start, end).catch(console.error);
  };

  const applyThisMonth = () => {
    const today = new Date();
    const start = formatDate(new Date(today.getFullYear(), today.getMonth(), 1));
    const end = formatDate(today);

    setDateFrom(start);
    setDateTo(end);
    load(start, end).catch(console.error);
  };

  const clearRange = () => {
    setDateFrom("");
    setDateTo("");
    load("", "").catch(console.error);
  };

  return (
    <div>
      <h1 style={{ marginTop: 0, fontSize: 42, marginBottom: 10 }}>
        Consola Printanista
      </h1>

      <div style={{ color: "#94a3b8", marginBottom: 24, fontSize: 18 }}>
        Base operativa, consulta por serie, importación y reportes.
      </div>

      <div style={sectionCard}>
        <div style={{ fontWeight: 700, marginBottom: 10, fontSize: 18 }}>
          Búsqueda rápida por serie
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <input
            value={serieInput}
            onChange={(e) => setSerieInput(e.target.value)}
            placeholder="Ej. T926Q130031"
            style={{
              flex: 1,
              background: "#0b1220",
              color: "#fff",
              border: "1px solid #334155",
              borderRadius: 12,
              padding: 14,
              fontSize: 18,
            }}
          />

          <button
            onClick={() => {
              setSerie(serieInput);
              openPage("consulta");
            }}
            style={primaryBtn}
          >
            Abrir
          </button>
        </div>
      </div>

      <div style={{ ...sectionCard, marginTop: 16 }}>
        <div style={{ fontWeight: 700, marginBottom: 14, fontSize: 18 }}>
          Rango de fechas
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "220px 220px auto",
            gap: 12,
            alignItems: "end",
          }}
        >
          <DateField
            label="Desde"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />

          <DateField
            label="Hasta"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button style={quickBtn} onClick={() => applyQuickRange(7)}>
              7 días
            </button>
            <button style={quickBtn} onClick={() => applyQuickRange(30)}>
              30 días
            </button>
            <button style={quickBtn} onClick={applyThisMonth}>
              Este mes
            </button>
            <button style={secondaryBtn} onClick={() => load()}>
              Aplicar
            </button>
            <button style={ghostBtn} onClick={clearRange}>
              Limpiar
            </button>
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: 16,
          marginTop: 16,
          marginBottom: 24,
        }}
      >
        <QuickCard
          title="Sin reportar"
          value={data?.quick?.sin_reportar ?? "-"}
          onClick={() => openPage("sinReportar")}
        />
        <QuickCard
          title="Reemplazos recientes"
          value={data?.quick?.reemplazos_recientes ?? "-"}
          onClick={() => openPage("reemplazos")}
        />
        <QuickCard
          title="Series repetidas"
          value={data?.quick?.series_repetidas ?? "-"}
          onClick={() => openPage("seriesRepetidas")}
        />
        <QuickCard
          title="Importación / Sync"
          value="Abrir"
          onClick={() => openPage("importacion")}
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 1fr",
          gap: 18,
        }}
      >
        <div style={sectionCard}>
          <div style={{ fontWeight: 800, fontSize: 20, marginBottom: 16 }}>
            Contadores
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0,1fr))",
              gap: 14,
              marginBottom: 18,
            }}
          >
            <MiniMetric
              title="Series activas"
              value={data?.contadores?.series_activas ?? 0}
            />
            <MiniMetric
              title="Último día reportado"
              value={data?.contadores?.ultimo_dia_reportado ?? "-"}
            />
            <MiniMetric
              title="Total registros"
              value={formatNumber(data?.contadores?.total_registros ?? 0)}
            />
          </div>

          <button
            onClick={() => openPage("contadores")}
            style={{
              ...secondaryBtn,
              marginBottom: 18,
            }}
          >
            Abrir módulo de contadores
          </button>

          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 12 }}>
            Evolución de documentos diarios
          </div>

          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={evolucion}>
                <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                <XAxis dataKey="fecha" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0b1220",
                    border: "1px solid #334155",
                    borderRadius: 10,
                    color: "#fff",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="total"
                  stroke="#fb7185"
                  fill="#fb7185"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={sectionCard}>
          <div style={{ fontWeight: 800, fontSize: 20, marginBottom: 16 }}>
            Alertas
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0,1fr))",
              gap: 14,
              marginBottom: 18,
            }}
          >
            <MiniMetric
              title="Total alertas"
              value={formatNumber(data?.alertas?.total_alertas ?? 0)}
            />
            <MiniMetric
              title="Equipos con alerta"
              value={formatNumber(data?.alertas?.equipos_con_alerta ?? 0)}
            />
            <MiniMetric
              title="Tipos de alerta"
              value={formatNumber(data?.alertas?.tipos_alerta ?? 0)}
            />
          </div>

          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 12 }}>
            Alertas por día
          </div>

          <div style={{ height: 170, marginBottom: 18 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={alertasDiarias}>
                <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                <XAxis dataKey="fecha" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0b1220",
                    border: "1px solid #334155",
                    borderRadius: 10,
                    color: "#fff",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="total"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.18}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 12 }}>
            Alertas por tipo
          </div>

          <div style={{ height: 170 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={alertasPorTipo}>
                <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                <XAxis dataKey="fecha" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0b1220",
                    border: "1px solid #334155",
                    borderRadius: 10,
                    color: "#fff",
                  }}
                />
                <Legend wrapperStyle={{ color: "#cbd5e1" }} />
                <Bar dataKey="suministro" name="Suministro" fill="#60a5fa" radius={[6, 6, 0, 0]} />
                <Bar dataKey="mantenimiento" name="Mantenimiento" fill="#c084fc" radius={[6, 6, 0, 0]} />
                <Bar dataKey="error" name="Error" fill="#f87171" radius={[6, 6, 0, 0]} />
                <Bar dataKey="otros" name="Otros" fill="#34d399" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function normalizeTipo(tipo) {
  const v = String(tipo || "").toLowerCase();

  if (v.includes("sumin")) return "suministro";
  if (v.includes("manten")) return "mantenimiento";
  if (v.includes("error")) return "error";
  return "otros";
}

function QuickCard({ title, value, onClick }) {
  return (
    <button onClick={onClick} style={quickCardStyle}>
      <div style={{ color: "#94a3b8", fontSize: 14 }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 800, marginTop: 10 }}>{value}</div>
    </button>
  );
}

function MiniMetric({ title, value }) {
  return (
    <div style={miniMetricStyle}>
      <div style={{ color: "#94a3b8", fontSize: 13 }}>{title}</div>
      <div style={{ fontSize: 20, fontWeight: 800, marginTop: 8 }}>{value}</div>
    </div>
  );
}

function shortDate(value) {
  if (!value) return "";
  return String(value).slice(5, 10);
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-PY").format(Number(value || 0));
}

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const sectionCard = {
  background: "#101827",
  border: "1px solid #1f2937",
  borderRadius: 16,
  padding: 18,
};

const quickCardStyle = {
  background: "#101827",
  color: "#fff",
  border: "1px solid #1f2937",
  borderRadius: 16,
  padding: 18,
  textAlign: "left",
  cursor: "pointer",
};

const miniMetricStyle = {
  background: "#0b1220",
  border: "1px solid #1f2937",
  borderRadius: 14,
  padding: 16,
};

const primaryBtn = {
  background: "#f43f5e",
  color: "#fff",
  border: "none",
  borderRadius: 12,
  padding: "14px 20px",
  fontWeight: 800,
  cursor: "pointer",
  fontSize: 16,
};

const secondaryBtn = {
  background: "#0b1220",
  color: "#fff",
  border: "1px solid #334155",
  borderRadius: 12,
  padding: "12px 16px",
  fontWeight: 700,
  cursor: "pointer",
};

const ghostBtn = {
  background: "transparent",
  color: "#cbd5e1",
  border: "1px solid #334155",
  borderRadius: 12,
  padding: "12px 16px",
  fontWeight: 700,
  cursor: "pointer",
};

const quickBtn = {
  background: "#0b1220",
  color: "#cbd5e1",
  border: "1px solid #334155",
  borderRadius: 12,
  padding: "12px 14px",
  fontWeight: 700,
  cursor: "pointer",
};