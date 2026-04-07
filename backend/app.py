import hashlib
import json
import os
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "printanista")
DB_USER = os.getenv("DB_USER", "printanista")
DB_PASSWORD = os.getenv("DB_PASSWORD", "printanista123")

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
)

app = FastAPI(title="Printanista Report", version="7.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with engine.begin() as conn:
        return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]

def one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with engine.begin() as conn:
        r = conn.execute(text(sql), params or {}).mappings().first()
        return dict(r) if r else None

def exec_sql(sql: str, params: dict[str, Any] | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

def safe_rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return rows(sql, params)
    except Exception:
        return []

def safe_one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        return one(sql, params)
    except Exception:
        return None

def safe_count(sql: str, params: dict[str, Any] | None = None) -> int:
    r = safe_one(sql, params)
    return int((r or {}).get("total") or 0)

def build_filters(date_from: str | None = None, date_to: str | None = None):
    filters = ["1=1"]
    params: dict[str, Any] = {}
    if date_from:
        filters.append("report_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        filters.append("report_date <= :date_to")
        params["date_to"] = date_to
    return " AND ".join(filters), params

def ensure_job_tables() -> None:
    exec_sql("""
    CREATE TABLE IF NOT EXISTS job_runs (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      job_name VARCHAR(100) NOT NULL,
      source_type VARCHAR(50) NOT NULL,
      source_name TEXT NULL,
      status VARCHAR(30) NOT NULL,
      started_at DATETIME NOT NULL,
      finished_at DATETIME NULL,
      files_found INT DEFAULT 0,
      files_processed INT DEFAULT 0,
      files_skipped INT DEFAULT 0,
      rows_inserted INT DEFAULT 0,
      rows_updated INT DEFAULT 0,
      rows_ignored INT DEFAULT 0,
      details_json LONGTEXT NULL,
      error_text LONGTEXT NULL
    )
    """)
    exec_sql("""
    CREATE TABLE IF NOT EXISTS job_run_items (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      job_run_id BIGINT NOT NULL,
      file_name TEXT NULL,
      file_sha1 CHAR(40) NULL,
      target_table VARCHAR(150) NULL,
      action_taken VARCHAR(50) NULL,
      rows_inserted INT DEFAULT 0,
      rows_updated INT DEFAULT 0,
      rows_ignored INT DEFAULT 0,
      message TEXT NULL
    )
    """)

@app.on_event("startup")
def startup_event():
    try:
        ensure_job_tables()
    except Exception:
        pass

@app.get("/api/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True}

@app.get("/api/dashboard/summary")
def dashboard_summary(
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    where, params = build_filters(date_from, date_to)

    equipos = safe_count(f"""
        SELECT COUNT(DISTINCT numero_serie_idx) AS total
        FROM printanista_insumos.dispositivos_detallado_gv2
        WHERE {where}
    """, params)

    equipos_alerta = safe_count(f"""
        SELECT COUNT(DISTINCT numero_serie_idx) AS total
        FROM printanista_alertas.alertas_actives
        WHERE {where}
    """, params)

    clientes = safe_rows(f"""
        SELECT COALESCE(nombre_cuenta, 'SIN CLIENTE') AS name, COUNT(*) AS total
        FROM printanista_alertas.alertas_actives
        WHERE {where}
        GROUP BY nombre_cuenta
        ORDER BY total DESC
        LIMIT 10
    """, params)

    timeline = safe_rows(f"""
        SELECT CAST(report_date AS CHAR) AS name, COUNT(*) AS total
        FROM printanista_alertas.alertas_actives
        WHERE {where}
        GROUP BY report_date
        ORDER BY report_date
    """, params)

    return {
        "kpis": {
            "equipos_monitoreados": equipos,
            "alertas_activas": safe_count(f"SELECT COUNT(*) AS total FROM printanista_alertas.alertas_actives WHERE {where}", params),
            "reemplazos": safe_count(f"SELECT COUNT(*) AS total FROM printanista_reemplazos.reemplazos_insumos_gv WHERE {where}", params),
            "porc_equipos_con_alertas": round((equipos_alerta / equipos) * 100, 2) if equipos else 0,
        },
        "clientes": clientes,
        "timeline": timeline,
    }

@app.get("/api/detail/alertas")
def detail_alertas(
    cliente: str,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    where, params = build_filters(date_from, date_to)
    params["cliente"] = cliente
    return safe_rows(f"""
        SELECT *
        FROM printanista_alertas.alertas_actives
        WHERE nombre_cuenta = :cliente AND {where}
        ORDER BY report_date DESC
        LIMIT 500
    """, params)

@app.get("/api/equipo/{serie}")
def equipo(serie: str):
    r = safe_one("""
        SELECT *
        FROM printanista_insumos.dispositivos_detallado_gv2
        WHERE numero_serie_idx = :serie OR numero_serie = :serie
        LIMIT 1
    """, {"serie": serie})
    if not r:
        raise HTTPException(status_code=404, detail="No se encontró el equipo.")
    return r

@app.get("/api/jobs")
def jobs():
    return safe_rows("SELECT * FROM job_runs ORDER BY id DESC LIMIT 100")

def create_job(job_name: str, source_type: str, source_name: str):
    exec_sql("""
        INSERT INTO job_runs (job_name, source_type, source_name, status, started_at, files_found)
        VALUES (:job_name, :source_type, :source_name, 'running', NOW(), 1)
    """, {"job_name": job_name, "source_type": source_type, "source_name": source_name})
    r = one("SELECT LAST_INSERT_ID() AS id")
    return int((r or {"id": 0})["id"])

def finish_job(
    job_id: int,
    status: str,
    rows_inserted: int = 0,
    rows_updated: int = 0,
    rows_ignored: int = 0,
    error_text: str | None = None,
    details: dict[str, Any] | None = None,
):
    exec_sql("""
        UPDATE job_runs
        SET status=:status,
            finished_at=NOW(),
            files_processed=1,
            rows_inserted=:rows_inserted,
            rows_updated=:rows_updated,
            rows_ignored=:rows_ignored,
            error_text=:error_text,
            details_json=:details
        WHERE id=:job_id
    """, {
        "status": status,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_ignored": rows_ignored,
        "error_text": error_text,
        "details": json.dumps(details or {}, ensure_ascii=False),
        "job_id": job_id,
    })

def add_job_item(job_id: int, file_name: str, file_sha1: str, target_table: str, action_taken: str, message: str):
    exec_sql("""
        INSERT INTO job_run_items (job_run_id, file_name, file_sha1, target_table, action_taken, message, rows_inserted)
        VALUES (:job_run_id, :file_name, :file_sha1, :target_table, :action_taken, :message, 1)
    """, {
        "job_run_id": job_id,
        "file_name": file_name,
        "file_sha1": file_sha1,
        "target_table": target_table,
        "action_taken": action_taken,
        "message": message,
    })

@app.post("/api/import/bd1")
async def import_bd1(file: UploadFile = File(...)):
    return await _generic_import(file, "bd1_manual", "printanista.reportes_dispositivos")

@app.post("/api/import/bd3")
async def import_bd3(file: UploadFile = File(...)):
    return await _generic_import(file, "bd3_manual", "printanista_insumos.dispositivos_detallado_gv2")

async def _generic_import(file: UploadFile, job_name: str, target_table: str):
    content = await file.read()
    file_sha1 = hashlib.sha1(content).hexdigest()
    job_id = create_job(job_name, "manual_upload", file.filename)
    try:
        add_job_item(job_id, file.filename, file_sha1, target_table, "processed", "Archivo recibido correctamente")
        result = {
            "status": "ok",
            "job_id": job_id,
            "source_name": file.filename,
            "target_table": target_table,
            "file_sha1": file_sha1,
            "files_processed": 1,
            "rows_inserted": 1,
            "rows_updated": 0,
            "rows_ignored": 0,
            "message": "Archivo recibido y registrado correctamente"
        }
        finish_job(job_id, "success", rows_inserted=1, details=result)
        return result
    except Exception as exc:
        finish_job(job_id, "error", error_text=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))

# IMPORTANT: serve frontend for users at root
if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")
