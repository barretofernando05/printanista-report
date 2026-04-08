import React from "react";

export default function DataTable({ rows = [], onRowClick }) {
  if (!rows.length) {
    return <div style={{ color: "#94a3b8" }}>Sin datos.</div>;
  }

  const cols = Object.keys(rows[0]);

  return (
    <div
      style={{
        width: "100%",
        overflowX: "auto",
        overflowY: "auto",
        maxWidth: "100%",
        border: "1px solid #1f2937",
        borderRadius: 12,
        background: "#0b1220",
      }}
    >
      <table
        style={{
          width: "max-content",
          minWidth: "100%",
          borderCollapse: "collapse",
          fontSize: 12,
        }}
      >
        <thead>
          <tr>
            {cols.map((c) => (
              <th
                key={c}
                style={{
                  textAlign: "left",
                  padding: "10px 12px",
                  background: "#101827",
                  color: "#94a3b8",
                  borderBottom: "1px solid #1f2937",
                  whiteSpace: "nowrap",
                  position: "sticky",
                  top: 0,
                  zIndex: 1,
                }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((r, idx) => (
            <tr
              key={idx}
              onClick={() => onRowClick?.(r)}
              style={{
                cursor: onRowClick ? "pointer" : "default",
              }}
            >
              {cols.map((c) => (
                <td
                  key={c}
                  style={{
                    padding: "8px 12px",
                    borderBottom: "1px solid #111827",
                    whiteSpace: "nowrap",
                    maxWidth: 240,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                  title={String(r[c] ?? "")}
                >
                  {String(r[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}