import React, { useState } from "react";
import AppShell from "./layout/AppShell";
import InicioPage from "./pages/InicioPage";
import ReemplazosPage from "./pages/ReemplazosPage";
import ContadoresPage from "./pages/ContadoresPage";
import SinReportarPage from "./pages/SinReportarPage";
import SeriesRepetidasPage from "./pages/SeriesRepetidasPage";
import ConsultaSeriePage from "./pages/ConsultaSeriePage";
import ImportacionPage from "./pages/ImportacionPage";
import HistorialPage from "./pages/HistorialPage";

export default function App() {
  const [page, setPage] = useState("inicio");
  const [serie, setSerie] = useState("");

  const openSerie = (s) => {
    if (!s) return;
    setSerie(String(s));
    setPage("consulta");
  };

  return (
    <AppShell page={page} setPage={setPage}>
      {page === "inicio" && <InicioPage openPage={setPage} setSerie={setSerie} />}
      {page === "reemplazos" && <ReemplazosPage openSerie={openSerie} />}
      {page === "contadores" && <ContadoresPage openSerie={openSerie} />}
      {page === "sinReportar" && <SinReportarPage openSerie={openSerie} />}
      {page === "seriesRepetidas" && <SeriesRepetidasPage openSerie={openSerie} />}
      {page === "consulta" && <ConsultaSeriePage serie={serie} setSerie={setSerie} />}
      {page === "importacion" && <ImportacionPage />}
      {page === "historial" && <HistorialPage />}
    </AppShell>
  );
}