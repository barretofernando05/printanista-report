import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "printanista")
DB_USER = os.getenv("DB_USER", "printanista")
DB_PASSWORD = os.getenv("DB_PASSWORD", "printanista123")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="Printanista Report", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]


def one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {}).mappings().first()
        return dict(result) if result else None


@app.get("/api/health")
def health() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB no disponible: {exc}") from exc


@app.get("/api/debug/tables")
def debug_tables() -> list[dict[str, Any]]:
    sql = """
    SELECT table_schema, table_name, table_type
    FROM information_schema.tables
    WHERE table_schema IN (
        'printanista',
        'printanista_alertas',
        'printanista_insumos',
        'printanista_reemplazos'
    )
    ORDER BY table_schema, table_name
    """
    try:
        return rows(sql)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/equipo/{serie}")
def consultar_equipo(serie: str) -> dict[str, Any]:
    params = {"serie": serie}

    try:
        resumen = one(
            """
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_con_alertas
            WHERE numero_serie = :serie
               OR numero_serie_idx = :serie
            LIMIT 1
            """,
            params,
        )

        if not resumen:
            resumen = one(
                """
                SELECT *
                FROM printanista_insumos.vw_equipo_insumos_resumen
                WHERE numero_serie = :serie
                   OR numero_serie_idx = :serie
                LIMIT 1
                """,
                params,
            )

        if not resumen:
            raise HTTPException(status_code=404, detail="No se encontró el equipo.")

        serie_idx = resumen.get("numero_serie_idx") or serie
        params2 = {"serie": serie, "serie_idx": serie_idx}

        detalle_insumos = rows(
            """
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_detalle
            WHERE numero_serie = :serie
               OR numero_serie_idx = :serie_idx
            ORDER BY report_date_reemplazo DESC, suministro ASC
            LIMIT 200
            """,
            params2,
        )

        alertas = rows(
            """
            SELECT *
            FROM printanista_alertas.vw_alertas_actives
            WHERE numero_serie_txt = :serie_idx
               OR numero_serie_txt = :serie
            ORDER BY report_date DESC, id DESC
            LIMIT 200
            """,
            params2,
        )

        reemplazos = rows(
            """
            SELECT *
            FROM printanista_reemplazos.vw_reemplazos_insumos_pct
            WHERE numero_serie = :serie
               OR numero_serie_idx = :serie_idx
            ORDER BY report_date DESC, id DESC
            LIMIT 200
            """,
            params2,
        )

        contadores = one(
            """
            SELECT
                n_mero_serie,
                nombre_cuenta,
                fabricante,
                modelo,
                direcci_n_ip,
                total_p_ginas_mono,
                total_p_ginas_color,
                _ltima_fecha_auditor_a_medidores,
                reportdate,
                sourcefile
            FROM printanista.reportes_dispositivos
            WHERE n_mero_serie = :serie
            ORDER BY id DESC
            LIMIT 1
            """,
            params,
        )

        return {
            "resumen": resumen,
            "insumos": detalle_insumos,
            "alertas": alertas,
            "reemplazos": reemplazos,
            "contadores": contadores,
        }
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/equipos")
def listar_equipos(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    try:
        return rows(
            f"""
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_con_alertas
            ORDER BY report_date_dispositivo DESC, nombre_cuenta ASC
            LIMIT {int(limit)}
            """
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/reports/overview")
def reports_overview() -> dict[str, Any]:
    try:
        return {
            "equipos_con_alertas": one(
                """
                SELECT COUNT(*) AS total
                FROM printanista_insumos.vw_equipo_insumos_con_alertas
                WHERE alertas_total > 0
                """
            )["total"],
            "alertas_activas": one(
                "SELECT COUNT(*) AS total FROM printanista_alertas.vw_alertas_actives"
            )["total"],
            "reemplazos": one(
                "SELECT COUNT(*) AS total FROM printanista_reemplazos.vw_reemplazos_insumos_pct"
            )["total"],
            "equipos_resumen": one(
                "SELECT COUNT(*) AS total FROM printanista_insumos.vw_equipo_insumos_resumen"
            )["total"],
        }
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")
