import React from "react";
export default function FilterPanel({ title, children }) {
  return (
    <aside style={{ width: 260, background: "#111827", border: "1px solid #1f2937", borderRadius: 14, padding: 16, alignSelf: "flex-start" }}>
      <div style={{ fontWeight: 700, marginBottom: 14 }}>{title}</div>
      <div style={{ display: "grid", gap: 12 }}>{children}</div>
    </aside>
  );
}
