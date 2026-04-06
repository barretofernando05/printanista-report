import os
from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="Printanista Report")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB no disponible: {str(e)}")


@app.get("/api/debug/tables")
def debug_tables():
    try:
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
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).mappings().all()
        return [dict(r) for r in rows]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/equipo/{serie}")
def consultar_equipo(serie: str):
    try:
        with engine.connect() as conn:
            # BD3 / Insumos - detalle principal del equipo
            equipo_sql = """
            SELECT *
            FROM printanista_insumos.dispositivos_detalle
            WHERE serie = :serie
               OR serial = :serie
               OR nro_serie = :serie
            LIMIT 1
            """
            equipo = conn.execute(text(equipo_sql), {"serie": serie}).mappings().first()

            if not equipo:
                raise HTTPException(status_code=404, detail="No se encontró el equipo.")

            # BD2 / Alertas
            alertas_sql = """
            SELECT *
            FROM printanista_alertas.alertas_actives
            WHERE serie = :serie
               OR serial = :serie
               OR nro_serie = :serie
            LIMIT 50
            """
            alertas = conn.execute(text(alertas_sql), {"serie": serie}).mappings().all()

            # BD4 / Reemplazos
            reemplazos_sql = """
            SELECT *
            FROM printanista_reemplazos.reemplazos_insumos
            WHERE serie = :serie
               OR serial = :serie
               OR nro_serie = :serie
            LIMIT 50
            """
            reemplazos = conn.execute(text(reemplazos_sql), {"serie": serie}).mappings().all()

            # BD1 / Core o reportes
            contadores_sql = """
            SELECT *
            FROM printanista.reportes_dispositivos
            WHERE serie = :serie
               OR serial = :serie
               OR nro_serie = :serie
            LIMIT 1
            """
            contadores = conn.execute(text(contadores_sql), {"serie": serie}).mappings().first()

            return {
                "equipo": dict(equipo) if equipo else None,
                "alertas": [dict(r) for r in alertas],
                "reemplazos": [dict(r) for r in reemplazos],
                "contadores": dict(contadores) if contadores else None
            }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/equipos")
def listar_equipos(limit: int = 100):
    try:
        sql = f"""
        SELECT *
        FROM printanista_insumos.dispositivos_detalle
        LIMIT {int(limit)}
        """
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).mappings().all()
        return [dict(r) for r in rows]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")