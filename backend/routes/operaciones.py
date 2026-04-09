from fastapi import APIRouter
from ..db import safe_rows, safe_one
from ..services.export_utils import excel_response

router = APIRouter(prefix="/api/operaciones", tags=["operaciones"])


def query_reemplazos(date_from=None, date_to=None, client_contains=None, limit=500):
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

    rows = safe_rows(
        f"""
        SELECT
            nombre_cuenta,
            fabricante,
            modelo,
            numero_serie,
            suministro,
            parte_oem,
            rendimiento,
            fecha_instalacion,
            contador_instalacion,
            nivel_instalacion,
            fecha_de_reemplazo,
            contador_al_reemplazo,
            nivel_al_reemplazo,
            rendimiento_objetivo,
            rendimiento_alcanzado,
            cobertura_alcanzada,
            nuevo_nivel_suministro,
            nivel_mas_reciente,
            fecha_est_de_vacio,
            nivel_instalacion_pct,
            nivel_al_reemplazo_pct
        FROM printanista_reemplazos.vw_reemplazos_insumos_pct
        WHERE {where}
        ORDER BY report_date DESC, fecha_de_reemplazo DESC
        LIMIT {limit}
        """,
        params,
    )
    return rows


def query_contadores(date_from=None, date_to=None, client_contains=None, limit=500):
    filters = ["1=1"]
    params = {}

    if date_from:
        filters.append("reportdate >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("reportdate <= :date_to")
        params["date_to"] = date_to

    if client_contains:
        filters.append("LOWER(COALESCE(nombre_cuenta,'')) LIKE :client_contains")
        params["client_contains"] = f"%{client_contains.lower()}%"

    where = " AND ".join(filters)

    rows = safe_rows(
        f"""
        SELECT
            n_mero_serie AS numero_serie,
            nombre_cuenta,
            fabricante,
            modelo,
            reportdate,
            total_p_ginas_mono,
            total_p_ginas_color,
            direcci_n_ip,
            _ltima_fecha_auditor_a_medidores,
            sourcefile
        FROM printanista.reportes_dispositivos
        WHERE {where}
        ORDER BY reportdate DESC
        LIMIT {limit}
        """,
        params,
    )

    summary = safe_one(
        f"""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT n_mero_serie) AS series,
            MAX(reportdate) AS ultimo_reporte
        FROM printanista.reportes_dispositivos
        WHERE {where}
        """,
        params,
    ) or {"total": 0, "series": 0, "ultimo_reporte": None}

    return rows, summary


def query_sin_reportar(min_days_no_report=60, client_contains=None, limit=5000):
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

    rows = safe_rows(
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
    return rows


def query_series_repetidas(min_distinct_clients=2, active_last_days=90, limit=5000):
    rows = safe_rows(
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
    return rows


def query_series_repetidas_clientes(serie: str):
    rows = safe_rows(
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
    return rows


@router.get("/reemplazos")
def reemplazos(date_from: str | None = None, date_to: str | None = None, client_contains: str | None = None, limit: int = 500):
    data = query_reemplazos(date_from, date_to, client_contains, limit)
    return {
        "summary": {
            "eventos": len(data),
            "innecesarios": 0,
            "no_nuevos": 0,
            "sin_alerta": 0,
        },
        "rows": data,
    }


@router.get("/reemplazos/export")
def reemplazos_export(date_from: str | None = None, date_to: str | None = None, client_contains: str | None = None, limit: int = 5000):
    rows = query_reemplazos(date_from, date_to, client_contains, limit)
    return excel_response(rows, "reemplazos_bd3")


@router.get("/contadores")
def contadores(date_from: str | None = None, date_to: str | None = None, client_contains: str | None = None, limit: int = 500):
    rows, summary = query_contadores(date_from, date_to, client_contains, limit)
    return {
        "summary": summary,
        "rows": rows,
    }


@router.get("/contadores/export")
def contadores_export(date_from: str | None = None, date_to: str | None = None, client_contains: str | None = None, limit: int = 5000):
    rows, _summary = query_contadores(date_from, date_to, client_contains, limit)
    return excel_response(rows, "contadores_bd1")


@router.get("/sin-reportar")
def sin_reportar(min_days_no_report: int = 60, client_contains: str | None = None, limit: int = 5000):
    data = query_sin_reportar(min_days_no_report, client_contains, limit)
    return {
        "summary": {"total": len(data)},
        "rows": data,
    }


@router.get("/sin-reportar/export")
def sin_reportar_export(min_days_no_report: int = 60, client_contains: str | None = None, limit: int = 10000):
    rows = query_sin_reportar(min_days_no_report, client_contains, limit)
    return excel_response(rows, "equipos_sin_reportar_bd1")


@router.get("/series-repetidas")
def series_repetidas(min_distinct_clients: int = 2, active_last_days: int = 90, limit: int = 5000):
    data = query_series_repetidas(min_distinct_clients, active_last_days, limit)
    return {
        "summary": {"series": len(data)},
        "rows": data,
    }


@router.get("/series-repetidas/export")
def series_repetidas_export(min_distinct_clients: int = 2, active_last_days: int = 90, limit: int = 10000):
    rows = query_series_repetidas(min_distinct_clients, active_last_days, limit)
    return excel_response(rows, "series_repetidas_bd1")


@router.get("/series-repetidas/{serie}/clientes")
def series_repetidas_clientes(serie: str):
    data = query_series_repetidas_clientes(serie)
    return {"rows": data}


@router.get("/series-repetidas/{serie}/clientes/export")
def series_repetidas_clientes_export(serie: str):
    rows = query_series_repetidas_clientes(serie)
    return excel_response(rows, f"series_repetidas_clientes_{serie}")