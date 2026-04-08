from fastapi import APIRouter, HTTPException
from ..db import safe_rows, safe_one

router = APIRouter(prefix="/api/serie", tags=["consulta"])


@router.get("/{serie}/resumen")
def resumen(serie: str):
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

    if not row:
        raise HTTPException(status_code=404, detail="No se encontró la serie.")

    return row


@router.get("/{serie}/insumos")
def insumos(serie: str):
    return {
        "rows": safe_rows(
            """
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_detalle
            WHERE numero_serie_idx = :serie OR numero_serie = :serie
            ORDER BY report_date DESC
            LIMIT 500
            """,
            {"serie": serie},
        )
    }


@router.get("/{serie}/alertas")
def alertas(serie: str):
    # Primero intentamos con la vista si existe y tiene la serie
    data = safe_rows(
        """
        SELECT *
        FROM printanista_alertas.vw_alertas_actives
        WHERE numero_serie_txt = :serie
        ORDER BY report_date DESC
        LIMIT 500
        """,
        {"serie": serie},
    )

    if data:
        return {"rows": data}

    # Fallback a tabla base parseando JSON
    data = safe_rows(
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
        LIMIT 500
        """,
        {"serie": serie},
    )

    return {"rows": data}


@router.get("/{serie}/reemplazos")
def reemplazos(serie: str):
    return {
        "rows": safe_rows(
            """
            SELECT *
            FROM printanista_reemplazos.vw_reemplazos_insumos_pct
            WHERE numero_serie = :serie
               OR numero_serie_idx = :serie
            ORDER BY report_date DESC
            LIMIT 500
            """,
            {"serie": serie},
        )
    }


@router.get("/{serie}/contadores")
def contadores(serie: str, date_from: str | None = None, date_to: str | None = None):
    filters = ["n_mero_serie = :serie"]
    params = {"serie": serie}

    if date_from:
        filters.append("reportdate >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("reportdate <= :date_to")
        params["date_to"] = date_to

    where = " AND ".join(filters)

    return {
        "rows": safe_rows(
            f"""
            SELECT *
            FROM printanista.reportes_dispositivos
            WHERE {where}
            ORDER BY reportdate DESC
            LIMIT 500
            """,
            params,
        )
    }