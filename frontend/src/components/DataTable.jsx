import React from "react";

export default function DataTable({ rows = [], onRowClick }) {
  if (!rows.length) return <div style={{ color: "#94a3b8" }}>Sin datos.</div>;
  const cols = Object.keys(rows[0]);
  return (
    <div style={{ overflow: "auto", border: "1px solid #1f2937", borderRadius: 10 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead><tr>{cols.map((c) => <th key={c} style={{ textAlign: "left", padding: "8px 10px", background: "#101827", color: "#94a3b8", borderBottom: "1px solid #1f2937", whiteSpace: "nowrap" }}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, idx) => (
            <tr key={idx} onClick={() => onRowClick?.(r)} style={{ cursor: onRowClick ? "pointer" : "default" }}>
              {cols.map((c) => <td key={c} style={{ padding: "8px 10px", borderBottom: "1px solid #111827", whiteSpace: "nowrap" }}>{String(r[c] ?? "")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
