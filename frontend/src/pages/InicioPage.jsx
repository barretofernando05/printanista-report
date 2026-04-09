import React, { useEffect, useMemo, useState } from "react";
import { fetchJson } from "../api";
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

  useEffect(() => {
    fetchJson("/api/dashboard/home").then(setData).catch(console.error);
  }, []);

  const evolucion = useMemo(
    () =>
      (data?.charts?.evolucion_diaria || []).map((r) => ({
        fecha: shortDate(r.fecha),
        total: Number(r.total || 0),
      })),
    [data]
  );

  const paginas = useMemo(
    () =>
      (data?.charts?.paginas_diarias || []).map((r) => ({
        fecha: shortDate(r.fecha),
        mono: Number(r.total_mono || 0),
        color: Number(r.total_color || 0),
      })),
    [data]
  );

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
                  fillOpacity={0.22}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={sectionCard}>
          <div style={{ fontWeight: 800, fontSize: 20, marginBottom: 16 }}>
            Distribución de páginas
          </div>

          <div style={{ height: 340 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={paginas}>
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
                <Bar dataKey="mono" name="Total mono" fill="#60a5fa" radius={[6, 6, 0, 0]} />
                <Bar dataKey="color" name="Total color" fill="#c084fc" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 14,
              marginTop: 12,
            }}
          >
            <MiniMetric
              title="Total mono"
              value={formatNumber(sumField(paginas, "mono"))}
            />
            <MiniMetric
              title="Total color"
              value={formatNumber(sumField(paginas, "color"))}
            />
          </div>
        </div>
      </div>
    </div>
  );
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

function sumField(rows, field) {
  return rows.reduce((acc, item) => acc + Number(item[field] || 0), 0);
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-PY").format(Number(value || 0));
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