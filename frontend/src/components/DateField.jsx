import React, { useRef } from "react";
import { CalendarDays } from "lucide-react";

export default function DateField({ label, value, onChange }) {
  const inputRef = useRef(null);

  const openPicker = () => {
    if (inputRef.current && typeof inputRef.current.showPicker === "function") {
      inputRef.current.showPicker();
    } else if (inputRef.current) {
      inputRef.current.focus();
      inputRef.current.click();
    }
  };

  return (
    <label style={{ display: "grid", gap: 6 }}>
      {label && <span style={{ fontSize: 13, color: "#cbd5e1" }}>{label}</span>}

      <div
        onClick={openPicker}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "#0b1220",
          color: "#fff",
          border: "1px solid #334155",
          borderRadius: 10,
          padding: "10px 12px",
          cursor: "pointer",
        }}
      >
        <input
          ref={inputRef}
          type="date"
          value={value}
          onChange={onChange}
          style={{
            flex: 1,
            background: "transparent",
            color: "#fff",
            border: "none",
            outline: "none",
            fontSize: 14,
            colorScheme: "dark",
            cursor: "pointer",
          }}
        />

        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            openPicker();
          }}
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
    </label>
  );
}