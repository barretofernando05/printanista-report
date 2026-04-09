from fastapi import APIRouter, Query
from ..db import safe_rows, safe_count, safe_one

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/home")
def home(
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    filters = ["1=1"]
    params = {}

    if date_from:
        filters.append("reportdate >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("reportdate <= :date_to")
        params["date_to"] = date_to

    where = " AND ".join(filters)

    quick = {
        "sin_reportar": safe_count(
            "SELECT COUNT(*) AS total FROM printanista.rpt_serie_status"
        ),
        "reemplazos_recientes": safe_count(
            f"""
            SELECT COUNT(*) AS total
            FROM printanista_reemplazos.vw_reemplazos_insumos_pct
            WHERE 1=1
              {"AND report_date >= :date_from" if date_from else ""}
              {"AND report_date <= :date_to" if date_to else ""}
            """,
            params,
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
        WHERE {where}
        """,
        params,
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
        WHERE {where}
        GROUP BY reportdate
        ORDER BY reportdate
        """,
        params,
    )

    paginas_diarias = safe_rows(
        f"""
        SELECT
            CAST(reportdate AS CHAR) AS fecha,
            COALESCE(SUM(total_p_ginas_mono), 0) AS total_mono,
            COALESCE(SUM(total_p_ginas_color), 0) AS total_color
        FROM printanista.reportes_dispositivos
        WHERE {where}
        GROUP BY reportdate
        ORDER BY reportdate
        """,
        params,
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