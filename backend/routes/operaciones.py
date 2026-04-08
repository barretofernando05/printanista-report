from fastapi import APIRouter
from ..db import safe_rows

router = APIRouter(prefix="/api/operaciones", tags=["operaciones"])


@router.get("/reemplazos")
def reemplazos(
    date_from: str | None = None,
    date_to: str | None = None,
    client_contains: str | None = None,
    limit: int = 500,
):
    filters = ["1=1"]
    params = {}

    if date_from:
        filters.append("report_date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("report_date <= :date_to")
        params["date_to"] = date_to

    if client_contains:
        filters.append("LOWER(COALESCE(nombre_cuenta,'')) LIKE :client_contains")
        params["client_contains"] = f"%{client_contains.lower()}%"

    where = " AND ".join(filters)

    data = safe_rows(
        f"""
        SELECT *
        FROM printanista_reemplazos.vw_reemplazos_insumos_pct
        WHERE {where}
        ORDER BY report_date DESC
        LIMIT {limit}
        """,
        params,
    )

    return {
        "summary": {
            "eventos": len(data),
            "innecesarios": 0,
            "no_nuevos": 0,
            "sin_alerta": 0,
        },
        "rows": data,
    }


@router.get("/sin-reportar")
def sin_reportar(
    min_days_no_report: int = 60,
    client_contains: str | None = None,
    limit: int = 5000,
):
    filters = [
        "last_report_date IS NOT NULL",
        "max_report_date IS NOT NULL",
        "DATEDIFF(max_report_date, last_report_date) >= :min_days_no_report",
    ]
    params = {"min_days_no_report": min_days_no_report}

    if client_contains:
        filters.append("LOWER(COALESCE(cliente_reciente,'')) LIKE :client_contains")
        params["client_contains"] = f"%{client_contains.lower()}%"

    where = " AND ".join(filters)

    data = safe_rows(
        f"""
        SELECT
            serie_norm AS serie,
            cliente_reciente AS cliente,
            modelo_reciente AS modelo,
            fabricante_reciente AS fabricante,
            last_audit_date AS ultima_auditoria,
            last_report_date AS ultimo_reporte,
            max_report_date,
            DATEDIFF(max_report_date, last_report_date) AS dias_sin_reportar,
            DATEDIFF(CURDATE(), last_report_date) AS dias_hasta_hoy
        FROM printanista.rpt_serie_status
        WHERE {where}
        ORDER BY dias_sin_reportar DESC, ultimo_reporte ASC
        LIMIT {limit}
        """,
        params,
    )

    return {
        "summary": {"total": len(data)},
        "rows": data,
    }


@router.get("/series-repetidas")
def series_repetidas(
    min_distinct_clients: int = 2,
    active_last_days: int = 90,
    limit: int = 5000,
):
    data = safe_rows(
        """
        SELECT
            serie_norm AS serie,
            COUNT(DISTINCT cliente_norm) AS clientes_distintos,
            SUM(apariciones) AS apariciones,
            MAX(last_seen) AS last_seen
        FROM printanista.rpt_serie_cliente
        WHERE last_seen IS NOT NULL
          AND last_seen >= CURDATE() - INTERVAL :active_last_days DAY
        GROUP BY serie_norm
        HAVING COUNT(DISTINCT cliente_norm) >= :min_distinct_clients
        ORDER BY clientes_distintos DESC, apariciones DESC, last_seen DESC
        LIMIT :limit
        """,
        {
            "min_distinct_clients": min_distinct_clients,
            "active_last_days": active_last_days,
            "limit": limit,
        },
    )

    return {
        "summary": {"series": len(data)},
        "rows": data,
    }


@router.get("/series-repetidas/{serie}/clientes")
def series_repetidas_clientes(serie: str):
    data = safe_rows(
        """
        SELECT
            serie_norm AS serie,
            cliente_norm AS cliente,
            apariciones,
            last_seen
        FROM printanista.rpt_serie_cliente
        WHERE serie_norm = :serie
        ORDER BY last_seen DESC, apariciones DESC, cliente_norm ASC
        """,
        {"serie": serie},
    )

    return {"rows": data}