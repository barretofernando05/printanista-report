from fastapi import APIRouter, Query
from ..db import safe_rows, safe_count
from ..services.common import build_filters

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/home")
def home():
    return {
        "quick": {
            "sin_reportar": safe_count("SELECT COUNT(*) AS total FROM printanista.rpt_serie_status"),
            "reemplazos_recientes": safe_count("SELECT COUNT(*) AS total FROM printanista_reemplazos.reemplazos_insumos_gv WHERE report_date >= CURDATE() - INTERVAL 30 DAY"),
            "series_repetidas": safe_count("SELECT COUNT(*) AS total FROM printanista.rpt_serie_cliente"),
        },
        "jobs": safe_rows("SELECT id, job_name, status, started_at, finished_at FROM job_runs ORDER BY id DESC LIMIT 10"),
    }

@router.get("/summary")
def summary(date_from: str | None = Query(default=None), date_to: str | None = Query(default=None)):
    where, params = build_filters(date_from, date_to)
    equipos = safe_count(f"SELECT COUNT(DISTINCT numero_serie_idx) AS total FROM printanista_insumos.dispositivos_detallado_gv2 WHERE {where}", params)
    equipos_alerta = safe_count(f"SELECT COUNT(DISTINCT numero_serie_txt) AS total FROM printanista_alertas.alertas_actives WHERE {where}", params)
    return {
        "kpis": {
            "equipos_monitoreados": equipos,
            "alertas_activas": safe_count(f"SELECT COUNT(*) AS total FROM printanista_alertas.alertas_actives WHERE {where}", params),
            "reemplazos": safe_count(f"SELECT COUNT(*) AS total FROM printanista_reemplazos.reemplazos_insumos_gv WHERE {where}", params),
            "porc_equipos_con_alertas": round((equipos_alerta / equipos) * 100, 2) if equipos else 0,
        },
        "clientes": safe_rows(f"SELECT COALESCE(nombre_cuenta,'SIN CLIENTE') AS name, COUNT(*) AS total FROM printanista_alertas.vw_alertas_dashboard WHERE {where} GROUP BY nombre_cuenta ORDER BY total DESC LIMIT 10", params),
        "modelos": safe_rows(f"SELECT COALESCE(modelo,'SIN MODELO') AS name, COUNT(*) AS total FROM printanista_alertas.vw_alertas_dashboard WHERE {where} AND COALESCE(fabricante,'')='RICOH' GROUP BY modelo ORDER BY total DESC LIMIT 10", params),
        "timeline": safe_rows(f"SELECT CAST(report_date AS CHAR) AS name, COUNT(*) AS total FROM printanista_alertas.alertas_actives WHERE {where} GROUP BY report_date ORDER BY report_date", params),
        "reemplazos_mes": safe_rows("SELECT DATE_FORMAT(report_date, '%Y-%m') AS name, COUNT(*) AS total FROM printanista_reemplazos.reemplazos_insumos_gv WHERE report_date IS NOT NULL GROUP BY DATE_FORMAT(report_date, '%Y-%m') ORDER BY name"),
        "equipos_modelo": safe_rows("SELECT COALESCE(modelo,'SIN MODELO') AS name, COUNT(*) AS total FROM printanista_insumos.dispositivos_detallado_gv2 GROUP BY modelo ORDER BY total DESC LIMIT 10"),
    }
