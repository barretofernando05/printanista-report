import React from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { CalendarDays } from "lucide-react";

export default function DateField({ label, value, onChange }) {
  const selectedDate = value ? new Date(`${value}T00:00:00`) : null;

  return (
    <div style={{ display: "grid", gap: 6, width: "100%" }}>
      {label ? (
        <div style={{ fontSize: 13, color: "#cbd5e1" }}>{label}</div>
      ) : null}

      <div style={{ position: "relative", width: "100%" }}>
        <DatePicker
          selected={selectedDate}
          onChange={(date) => {
            if (!date) {
              onChange({ target: { value: "" } });
              return;
            }

            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const day = String(date.getDate()).padStart(2, "0");
            onChange({ target: { value: `${year}-${month}-${day}` } });
          }}
          dateFormat="yyyy-MM-dd"
          placeholderText="yyyy-mm-dd"
          className="date-input-custom"
          popperPlacement="bottom-start"
        />

        <CalendarDays
          size={18}
          style={{
            position: "absolute",
            right: 12,
            top: "50%",
            transform: "translateY(-50%)",
            pointerEvents: "none",
            color: "#94a3b8",
          }}
        />
      </div>
    </div>
  );
}