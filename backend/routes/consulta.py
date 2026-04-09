from fastapi import APIRouter, HTTPException
from ..db import safe_rows, safe_one
from ..services.export_utils import excel_response

router = APIRouter(prefix="/api/serie", tags=["consulta"])


def query_resumen(serie: str):
    row = safe_one(
        """
        SELECT *
        FROM printanista_insumos.vw_equipo_insumos_con_alertas
        WHERE numero_serie_idx = :serie OR numero_serie = :serie
        ORDER BY report_date DESC
        LIMIT 1
        """,
        {"serie": serie},
    )

    if not row:
        row = safe_one(
            """
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_resumen
            WHERE numero_serie_idx = :serie OR numero_serie = :serie
            ORDER BY report_date DESC
            LIMIT 1
            """,
            {"serie": serie},
        )
    return row


def query_insumos(serie: str):
    return safe_rows(
        """
        SELECT *
        FROM printanista_insumos.vw_equipo_insumos_detalle
        WHERE numero_serie_idx = :serie OR numero_serie = :serie
        ORDER BY report_date DESC
        LIMIT 5000
        """,
        {"serie": serie},
    )


def query_alertas(serie: str):
    data = safe_rows(
        """
        SELECT *
        FROM printanista_alertas.vw_alertas_actives
        WHERE numero_serie_txt = :serie
        ORDER BY report_date DESC
        LIMIT 5000
        """,
        {"serie": serie},
    )

    if data:
        return data

    return safe_rows(
        """
        SELECT
          report_date,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Tipo')) AS tipo,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Item')) AS item,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Rendimiento')) AS rendimiento,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Nivel_Suministro_(%)')) AS nivel_suministro_pct,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Fecha_de_Vacio')) AS fecha_de_vacio,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Estado(s)_Error_Impresora')) AS estados_error_impresora,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Activador(es)_de_alerta')) AS activadores_alerta,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Estado(s)_Activador(es)')) AS estados_activadores,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Detectado')) AS detectado,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Nombre_Cuenta')) AS nombre_cuenta,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Fabricante')) AS fabricante,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Modelo')) AS modelo,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Dirección_IP')) AS direccion_ip,
          JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Ubicación')) AS ubicacion,
          numero_serie_txt
        FROM printanista_alertas.alertas_actives
        WHERE numero_serie_txt = :serie
        ORDER BY report_date DESC
        LIMIT 5000
        """,
        {"serie": serie},
    )


def query_reemplazos(serie: str):
    return safe_rows(
        """
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
        WHERE numero_serie = :serie OR numero_serie_idx = :serie
        ORDER BY report_date DESC
        LIMIT 5000
        """,
        {"serie": serie},
    )


def query_contadores(serie: str, date_from: str | None = None, date_to: str | None = None):
    filters = ["n_mero_serie = :serie"]
    params = {"serie": serie}

    if date_from:
        filters.append("reportdate >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("reportdate <= :date_to")
        params["date_to"] = date_to

    where = " AND ".join(filters)

    return safe_rows(
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
        LIMIT 5000
        """,
        params,
    )


@router.get("/{serie}/resumen")
def resumen(serie: str):
    row = query_resumen(serie)
    if not row:
        raise HTTPException(status_code=404, detail="No se encontró la serie.")
    return row


@router.get("/{serie}/resumen/export")
def resumen_export(serie: str):
    row = query_resumen(serie)
    if not row:
        raise HTTPException(status_code=404, detail="No se encontró la serie.")
    return excel_response([row], f"resumen_{serie}")


@router.get("/{serie}/insumos")
def insumos(serie: str):
    return {"rows": query_insumos(serie)}


@router.get("/{serie}/insumos/export")
def insumos_export(serie: str):
    return excel_response(query_insumos(serie), f"insumos_{serie}")


@router.get("/{serie}/alertas")
def alertas(serie: str):
    return {"rows": query_alertas(serie)}


@router.get("/{serie}/alertas/export")
def alertas_export(serie: str):
    return excel_response(query_alertas(serie), f"alertas_{serie}")


@router.get("/{serie}/reemplazos")
def reemplazos(serie: str):
    return {"rows": query_reemplazos(serie)}


@router.get("/{serie}/reemplazos/export")
def reemplazos_export(serie: str):
    return excel_response(query_reemplazos(serie), f"reemplazos_{serie}")


@router.get("/{serie}/contadores")
def contadores(serie: str, date_from: str | None = None, date_to: str | None = None):
    return {"rows": query_contadores(serie, date_from, date_to)}


@router.get("/{serie}/contadores/export")
def contadores_export(serie: str, date_from: str | None = None, date_to: str | None = None):
    return excel_response(query_contadores(serie, date_from, date_to), f"contadores_{serie}")