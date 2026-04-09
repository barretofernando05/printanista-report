from fastapi import APIRouter, Query
from ..db import safe_rows, safe_count, safe_one
from ..services.common import build_filters

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/home")
def home():
    quick = {
        "sin_reportar": safe_count(
            "SELECT COUNT(*) AS total FROM printanista.rpt_serie_status"
        ),
        "reemplazos_recientes": safe_count(
            """
            SELECT COUNT(*) AS total
            FROM printanista_reemplazos.vw_reemplazos_insumos_pct
            WHERE report_date >= CURDATE() - INTERVAL 30 DAY
            """
        ),
        "series_repetidas": safe_count(
            """
            SELECT COUNT(DISTINCT serie_norm) AS total
            FROM printanista.rpt_serie_cliente
            """
        ),
    }

    contadores = safe_one(
        """
        SELECT
            COUNT(*) AS total_registros,
            COUNT(DISTINCT n_mero_serie) AS series_activas,
            MAX(reportdate) AS ultimo_dia_reportado
        FROM printanista.reportes_dispositivos
        """
    ) or {
        "total_registros": 0,
        "series_activas": 0,
        "ultimo_dia_reportado": None,
    }

    evolucion_diaria = safe_rows(
        """
        SELECT
            CAST(reportdate AS CHAR) AS fecha,
            COUNT(*) AS total
        FROM printanista.reportes_dispositivos
        WHERE reportdate >= CURDATE() - INTERVAL 30 DAY
        GROUP BY reportdate
        ORDER BY reportdate
        """
    )

    paginas_diarias = safe_rows(
        """
        SELECT
            CAST(reportdate AS CHAR) AS fecha,
            COALESCE(SUM(total_p_ginas_mono), 0) AS total_mono,
            COALESCE(SUM(total_p_ginas_color), 0) AS total_color
        FROM printanista.reportes_dispositivos
        WHERE reportdate >= CURDATE() - INTERVAL 30 DAY
        GROUP BY reportdate
        ORDER BY reportdate
        """
    )

    jobs = safe_rows(
        """
        SELECT id, job_name, status, started_at, finished_at
        FROM job_runs
        ORDER BY id DESC
        LIMIT 10
        """
    )

    return {
        "quick": quick,
        "contadores": contadores,
        "charts": {
            "evolucion_diaria": evolucion_diaria,
            "paginas_diarias": paginas_diarias,
        },
        "jobs": jobs,
    }


@router.get("/summary")
def summary(
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    where, params = build_filters(date_from, date_to)

    equipos = safe_count(
        f"""
        SELECT COUNT(DISTINCT numero_serie_idx) AS total
        FROM printanista_insumos.vw_equipo_insumos_resumen
        WHERE {where}
        """,
        params,
    )

    equipos_con_alerta = safe_count(
        f"""
        SELECT COUNT(DISTINCT numero_serie_idx) AS total
        FROM printanista_insumos.vw_equipo_insumos_con_alertas
        WHERE {where}
        """,
        params,
    )

    clientes = safe_rows(
        f"""
        SELECT COALESCE(nombre_cuenta, 'SIN CLIENTE') AS name, COUNT(*) AS total
        FROM printanista_insumos.vw_equipo_insumos_con_alertas
        WHERE {where}
        GROUP BY nombre_cuenta
        ORDER BY total DESC
        LIMIT 10
        """,
        params,
    )

    modelos = safe_rows(
        f"""
        SELECT COALESCE(modelo, 'SIN MODELO') AS name, COUNT(*) AS total
        FROM printanista_insumos.vw_equipo_insumos_con_alertas
        WHERE {where} AND COALESCE(fabricante, '') = 'RICOH'
        GROUP BY modelo
        ORDER BY total DESC
        LIMIT 10
        """,
        params,
    )

    timeline = safe_rows(
        f"""
        SELECT CAST(report_date AS CHAR) AS name, COUNT(*) AS total
        FROM printanista_insumos.vw_equipo_insumos_con_alertas
        WHERE {where}
        GROUP BY report_date
        ORDER BY report_date
        """,
        params,
    )

    reemplazos_mes = safe_rows(
        """
        SELECT DATE_FORMAT(report_date, '%Y-%m') AS name, COUNT(*) AS total
        FROM printanista_reemplazos.vw_reemplazos_insumos_pct
        WHERE report_date IS NOT NULL
        GROUP BY DATE_FORMAT(report_date, '%Y-%m')
        ORDER BY name
        """
    )

    equipos_modelo = safe_rows(
        """
        SELECT COALESCE(modelo, 'SIN MODELO') AS name, COUNT(*) AS total
        FROM printanista_insumos.vw_equipo_insumos_resumen
        GROUP BY modelo
        ORDER BY total DESC
        LIMIT 10
        """
    )

    return {
        "kpis": {
            "equipos_monitoreados": equipos,
            "alertas_activas": safe_count(
                f"""
                SELECT COUNT(*) AS total
                FROM printanista_insumos.vw_equipo_insumos_con_alertas
                WHERE {where}
                """,
                params,
            ),
            "reemplazos": safe_count(
                f"""
                SELECT COUNT(*) AS total
                FROM printanista_reemplazos.vw_reemplazos_insumos_pct
                WHERE {where}
                """,
                params,
            ),
            "porc_equipos_con_alertas": round((equipos_con_alerta / equipos) * 100, 2)
            if equipos
            else 0,
        },
        "clientes": clientes,
        "modelos": modelos,
        "timeline": timeline,
        "reemplazos_mes": reemplazos_mes,
        "equipos_modelo": equipos_modelo,
    }