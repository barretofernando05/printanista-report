import React, { useEffect, useState } from "react";
import { fetchJson } from "../api";
import DataTable from "../components/DataTable";

export default function HistorialPage() {
  const [jobs, setJobs] = useState([]);
  useEffect(() => { fetchJson("/api/jobs").then(setJobs).catch(console.error); }, []);
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Historial</h1>
      <div style={{ background: "#101827", border: "1px solid #1f2937", borderRadius: 14, padding: 16 }}>
        <DataTable rows={jobs} />
      </div>
    </div>
  );
}
