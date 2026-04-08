import React, { useRef } from "react";
import { CalendarDays } from "lucide-react";

export default function DateField({ label, value, onChange }) {
  const inputRef = useRef(null);

  const openPicker = () => {
    const el = inputRef.current;
    if (!el) return;

    if (typeof el.showPicker === "function") {
      el.showPicker();
      return;
    }

    el.focus();
    el.click();
  };

  return (
    <div style={{ display: "grid", gap: 6, width: "100%" }}>
      {label && (
        <div style={{ fontSize: 13, color: "#cbd5e1" }}>
          {label}
        </div>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "#0b1220",
          color: "#fff",
          border: "1px solid #334155",
          borderRadius: 10,
          padding: "10px 12px",
          width: "100%",
        }}
      >
        <input
          ref={inputRef}
          type="date"
          value={value}
          onChange={onChange}
          style={{
            flex: 1,
            minWidth: 0,
            background: "transparent",
            color: "#fff",
            border: "none",
            outline: "none",
            fontSize: 14,
            colorScheme: "dark",
          }}
        />

        <button
          type="button"
          onClick={openPicker}
          style={{
            background: "transparent",
            border: "none",
            color: "#cbd5e1",
            padding: 0,
            display: "flex",
            alignItems: "center",
            cursor: "pointer",
          }}
        >
          <CalendarDays size={18} />
        </button>
      </div>
    </div>
  );
}