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

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="Printanista Report", version="2.0.0")

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


def get_columns(schema: str, table: str) -> set[str]:
    sql = """
    SELECT COLUMN_NAME
    FROM information_schema.columns
    WHERE table_schema = :schema
      AND table_name = :table
    """
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(text(sql), {"schema": schema, "table": table}).all()}


def pick_first(columns: set[str], candidates: list[str]) -> str | None:
    for col in candidates:
        if col in columns:
            return col
    return None


def build_where(columns: set[str], candidates: list[str], param_name: str = "serie") -> tuple[str, str | None]:
    col = pick_first(columns, candidates)
    if not col:
        return "1=0", None
    return f"`{col}` = :{param_name}", col


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
    try:
        return rows(
            """
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
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/debug/columns")
def debug_columns() -> dict[str, list[str]]:
    targets = [
        ("printanista_insumos", "vw_equipo_insumos_con_alertas"),
        ("printanista_insumos", "vw_equipo_insumos_resumen"),
        ("printanista_insumos", "vw_equipo_insumos_detalle"),
        ("printanista_alertas", "vw_alertas_actives"),
        ("printanista_reemplazos", "vw_reemplazos_insumos_pct"),
        ("printanista", "reportes_dispositivos"),
    ]
    data = {}
    try:
        for schema, table in targets:
            data[f"{schema}.{table}"] = sorted(get_columns(schema, table))
        return data
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/equipo/{serie}")
def consultar_equipo(serie: str) -> dict[str, Any]:
    try:
        resumen_cols = get_columns("printanista_insumos", "vw_equipo_insumos_con_alertas")
        resumen_where, _ = build_where(
            resumen_cols, ["numero_serie", "numero_serie_idx", "n_mero_serie", "serial", "serie"]
        )

        resumen = one(
            f"""
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_con_alertas
            WHERE {resumen_where}
            LIMIT 1
            """,
            {"serie": serie},
        )

        if not resumen:
            resumen_cols = get_columns("printanista_insumos", "vw_equipo_insumos_resumen")
            resumen_where, _ = build_where(
                resumen_cols, ["numero_serie", "numero_serie_idx", "n_mero_serie", "serial", "serie"]
            )
            resumen = one(
                f"""
                SELECT *
                FROM printanista_insumos.vw_equipo_insumos_resumen
                WHERE {resumen_where}
                LIMIT 1
                """,
                {"serie": serie},
            )

        if not resumen:
            raise HTTPException(status_code=404, detail="No se encontró el equipo.")

        serie_val = (
            resumen.get("numero_serie")
            or resumen.get("numero_serie_idx")
            or resumen.get("n_mero_serie")
            or resumen.get("serial")
            or resumen.get("serie")
            or serie
        )

        detalle_cols = get_columns("printanista_insumos", "vw_equipo_insumos_detalle")
        detalle_where, _ = build_where(
            detalle_cols, ["numero_serie", "numero_serie_idx", "n_mero_serie", "serial", "serie"], "serie_val"
        )
        detalle_order = []
        for col in ["report_date_reemplazo", "fecha_de_reemplazo", "report_date", "id"]:
            if col in detalle_cols:
                detalle_order.append(f"`{col}` DESC")
        if "suministro" in detalle_cols:
            detalle_order.append("`suministro` ASC")
        order_sql = ", ".join(detalle_order) if detalle_order else "1"

        insumos = rows(
            f"""
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_detalle
            WHERE {detalle_where}
            ORDER BY {order_sql}
            LIMIT 200
            """,
            {"serie_val": serie_val},
        )

        alertas_cols = get_columns("printanista_alertas", "vw_alertas_actives")
        alertas_where, _ = build_where(
            alertas_cols,
            ["numero_serie", "numero_serie_idx", "numero_serie_txt", "n_mero_serie", "serial", "serie"],
            "serie_val",
        )
        alertas_order = []
        for col in ["report_date", "fecha", "id"]:
            if col in alertas_cols:
                alertas_order.append(f"`{col}` DESC")
        alertas_order_sql = ", ".join(alertas_order) if alertas_order else "1"

        alertas = rows(
            f"""
            SELECT *
            FROM printanista_alertas.vw_alertas_actives
            WHERE {alertas_where}
            ORDER BY {alertas_order_sql}
            LIMIT 200
            """,
            {"serie_val": serie_val},
        )

        reemplazos_cols = get_columns("printanista_reemplazos", "vw_reemplazos_insumos_pct")
        reemplazos_where, _ = build_where(
            reemplazos_cols, ["numero_serie", "numero_serie_idx", "n_mero_serie", "serial", "serie"], "serie_val"
        )
        reemplazos_order = []
        for col in ["report_date", "fecha_de_reemplazo", "id"]:
            if col in reemplazos_cols:
                reemplazos_order.append(f"`{col}` DESC")
        reemplazos_order_sql = ", ".join(reemplazos_order) if reemplazos_order else "1"

        reemplazos = rows(
            f"""
            SELECT *
            FROM printanista_reemplazos.vw_reemplazos_insumos_pct
            WHERE {reemplazos_where}
            ORDER BY {reemplazos_order_sql}
            LIMIT 200
            """,
            {"serie_val": serie_val},
        )

        cont_cols = get_columns("printanista", "reportes_dispositivos")
        cont_where, _ = build_where(
            cont_cols, ["n_mero_serie", "numero_serie", "serial", "serie"], "serie_val"
        )
        cont_select_candidates = [
            "n_mero_serie",
            "nombre_cuenta",
            "fabricante",
            "modelo",
            "direcci_n_ip",
            "total_p_ginas_mono",
            "total_p_ginas_color",
            "_ltima_fecha_auditor_a_medidores",
            "reportdate",
            "sourcefile",
        ]
        cont_select = ", ".join(f"`{c}`" for c in cont_select_candidates if c in cont_cols) or "*"
        cont_order = "ORDER BY `id` DESC" if "id" in cont_cols else ""

        contadores = one(
            f"""
            SELECT {cont_select}
            FROM printanista.reportes_dispositivos
            WHERE {cont_where}
            {cont_order}
            LIMIT 1
            """,
            {"serie_val": serie_val},
        )

        return {
            "resumen": resumen,
            "insumos": insumos,
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
        cols = get_columns("printanista_insumos", "vw_equipo_insumos_con_alertas")
        order_col = pick_first(cols, ["report_date_dispositivo", "report_date", "fecha", "id"])
        order_sql = f"ORDER BY `{order_col}` DESC" if order_col else ""
        return rows(
            f"""
            SELECT *
            FROM printanista_insumos.vw_equipo_insumos_con_alertas
            {order_sql}
            LIMIT {int(limit)}
            """
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/reports/overview")
def reports_overview() -> dict[str, Any]:
    try:
        resumen_cols = get_columns("printanista_insumos", "vw_equipo_insumos_con_alertas")
        if "alertas_total" in resumen_cols:
            equipos_con_alertas = one(
                """
                SELECT COUNT(*) AS total
                FROM printanista_insumos.vw_equipo_insumos_con_alertas
                WHERE alertas_total > 0
                """
            )["total"]
        else:
            equipos_con_alertas = None

        return {
            "equipos_con_alertas": equipos_con_alertas,
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
