from fastapi import APIRouter, Query
from ..db import safe_rows, safe_count, safe_one

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/home")
def home(
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    report_filters = ["1=1"]
    report_params = {}

    if date_from:
        report_filters.append("reportdate >= :date_from")
        report_params["date_from"] = date_from

    if date_to:
        report_filters.append("reportdate <= :date_to")
        report_params["date_to"] = date_to

    report_where = " AND ".join(report_filters)

    repl_filters = ["1=1"]
    repl_params = {}

    if date_from:
        repl_filters.append("report_date >= :date_from")
        repl_params["date_from"] = date_from

    if date_to:
        repl_filters.append("report_date <= :date_to")
        repl_params["date_to"] = date_to

    repl_where = " AND ".join(repl_filters)

    quick = {
        "sin_reportar": safe_count(
            "SELECT COUNT(*) AS total FROM printanista.rpt_serie_status"
        ),
        "reemplazos_recientes": safe_count(
            f"""
            SELECT COUNT(*) AS total
            FROM printanista_reemplazos.vw_reemplazos_insumos_pct
            WHERE {repl_where}
            """,
            repl_params,
        ),
        "series_repetidas": safe_count(
            """
            SELECT COUNT(DISTINCT serie_norm) AS total
            FROM printanista.rpt_serie_cliente
            """
        ),
    }

    contadores = safe_one(
        f"""
        SELECT
            COUNT(*) AS total_registros,
            COUNT(DISTINCT n_mero_serie) AS series_activas,
            MAX(reportdate) AS ultimo_dia_reportado
        FROM printanista.reportes_dispositivos
        WHERE {report_where}
        """,
        report_params,
    ) or {
        "total_registros": 0,
        "series_activas": 0,
        "ultimo_dia_reportado": None,
    }

    evolucion_diaria = safe_rows(
        f"""
        SELECT
            CAST(reportdate AS CHAR) AS fecha,
            COUNT(*) AS total
        FROM printanista.reportes_dispositivos
        WHERE {report_where}
        GROUP BY reportdate
        ORDER BY reportdate
        """,
        report_params,
    )

    paginas_diarias = safe_rows(
        f"""
        WITH daily_last AS (
            SELECT
                n_mero_serie,
                reportdate,
                MAX(COALESCE(total_p_ginas_mono, 0)) AS total_mono,
                MAX(COALESCE(total_p_ginas_color, 0)) AS total_color
            FROM printanista.reportes_dispositivos
            WHERE {report_where}
            GROUP BY n_mero_serie, reportdate
        ),
        daily_diff AS (
            SELECT
                n_mero_serie,
                reportdate,
                total_mono,
                total_color,
                total_mono - LAG(total_mono) OVER (
                    PARTITION BY n_mero_serie
                    ORDER BY reportdate
                ) AS mono_diff,
                total_color - LAG(total_color) OVER (
                    PARTITION BY n_mero_serie
                    ORDER BY reportdate
                ) AS color_diff
            FROM daily_last
        )
        SELECT
            CAST(reportdate AS CHAR) AS fecha,
            COALESCE(SUM(CASE WHEN mono_diff >= 0 THEN mono_diff ELSE 0 END), 0) AS total_mono,
            COALESCE(SUM(CASE WHEN color_diff >= 0 THEN color_diff ELSE 0 END), 0) AS total_color
        FROM daily_diff
        GROUP BY reportdate
        ORDER BY reportdate
        """,
        report_params,
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
        "filters": {
            "date_from": date_from,
            "date_to": date_to,
        },
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
    filters = ["1=1"]
    params = {}

    if date_from:
        filters.append("report_date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("report_date <= :date_to")
        params["date_to"] = date_to

    where = " AND ".join(filters)

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