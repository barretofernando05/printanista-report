import React, { useMemo, useState } from "react";

export default function DataTable({
  rows = [],
  onRowClick,
  pageSize = 25,
  title = "",
}) {
  const [page, setPage] = useState(1);

  const cols = useMemo(() => (rows.length ? Object.keys(rows[0]) : []), [rows]);
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const currentPage = Math.min(page, totalPages);

  const pagedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, currentPage, pageSize]);

  if (!rows.length) {
    return (
      <div
        style={{
          color: "#94a3b8",
          background: "#0b1220",
          border: "1px solid #1f2937",
          borderRadius: 14,
          padding: 18,
        }}
      >
        Sin datos.
      </div>
    );
  }

  return (
    <div
      style={{
        width: "100%",
        minWidth: 0,
      }}
    >
      {title && (
        <div
          style={{
            marginBottom: 10,
            fontSize: 14,
            color: "#94a3b8",
          }}
        >
          {title}
        </div>
      )}

      <div
        style={{
          width: "100%",
          minWidth: 0,
          overflowX: "auto",
          overflowY: "auto",
          border: "1px solid #1f2937",
          borderRadius: 14,
          background: "#0b1220",
        }}
      >
        <table
          style={{
            width: "max-content",
            minWidth: "100%",
            borderCollapse: "collapse",
            fontSize: 13,
            lineHeight: 1.35,
          }}
        >
          <thead>
            <tr>
              {cols.map((c) => (
                <th
                  key={c}
                  style={{
                    textAlign: "left",
                    padding: "12px 14px",
                    background: "#101827",
                    color: "#cbd5e1",
                    borderBottom: "1px solid #1f2937",
                    whiteSpace: "nowrap",
                    position: "sticky",
                    top: 0,
                    zIndex: 1,
                    fontWeight: 700,
                  }}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {pagedRows.map((r, idx) => (
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
                    title={String(r[c] ?? "")}
                    style={{
                      padding: "11px 14px",
                      borderBottom: "1px solid #111827",
                      whiteSpace: "nowrap",
                      maxWidth: 280,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      color: "#e5e7eb",
                    }}
                  >
                    {String(r[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        style={{
          marginTop: 12,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ color: "#94a3b8", fontSize: 13 }}>
          Mostrando {pagedRows.length} de {rows.length} filas
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            style={pagerBtn(currentPage === 1)}
          >
            Anterior
          </button>

          <div style={{ color: "#cbd5e1", fontSize: 13 }}>
            Página {currentPage} de {totalPages}
          </div>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            style={pagerBtn(currentPage === totalPages)}
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}

function pagerBtn(disabled) {
  return {
    background: disabled ? "#111827" : "#ef4444",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "8px 12px",
    fontWeight: 700,
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.45 : 1,
  };
}