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

    alert_filters = ["1=1"]
    alert_params = {}

    if date_from:
        alert_filters.append("report_date >= :date_from")
        alert_params["date_from"] = date_from

    if date_to:
        alert_filters.append("report_date <= :date_to")
        alert_params["date_to"] = date_to

    alert_where = " AND ".join(alert_filters)

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

    alertas_diarias = safe_rows(
        f"""
        SELECT
            CAST(report_date AS CHAR) AS fecha,
            COUNT(*) AS total
        FROM printanista_alertas.alertas_actives
        WHERE {alert_where}
        GROUP BY report_date
        ORDER BY report_date
        """,
        alert_params,
    )

    alertas_por_tipo_diaria = safe_rows(
        f"""
        SELECT
            CAST(report_date AS CHAR) AS fecha,
            COALESCE(JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Tipo')), 'Sin tipo') AS tipo,
            COUNT(*) AS total
        FROM printanista_alertas.alertas_actives
        WHERE {alert_where}
        GROUP BY report_date,
                 COALESCE(JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Tipo')), 'Sin tipo')
        ORDER BY report_date
        """,
        alert_params,
    )

    resumen_alertas = safe_one(
        f"""
        SELECT
            COUNT(*) AS total_alertas,
            COUNT(DISTINCT numero_serie_txt) AS equipos_con_alerta,
            COUNT(DISTINCT COALESCE(JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Tipo')), 'Sin tipo')) AS tipos_alerta
        FROM printanista_alertas.alertas_actives
        WHERE {alert_where}
        """,
        alert_params,
    ) or {
        "total_alertas": 0,
        "equipos_con_alerta": 0,
        "tipos_alerta": 0,
    }

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
        "alertas": resumen_alertas,
        "charts": {
            "evolucion_diaria": evolucion_diaria,
            "alertas_diarias": alertas_diarias,
            "alertas_por_tipo_diaria": alertas_por_tipo_diaria,
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