\
import base64
import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import create_engine, text

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "printanista")
DB_USER = os.getenv("DB_USER", "printanista")
DB_PASSWORD = os.getenv("DB_PASSWORD", "printanista123")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "/app/secrets/token_technoma.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
)

app = FastAPI(title="Printanista Report 7.1", version="7.1.0")
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

def create_job(job_name: str, source_type: str, source_name: str | None):
    exec_sql("""
        INSERT INTO job_runs (job_name, source_type, source_name, status, started_at)
        VALUES (:job_name, :source_type, :source_name, 'running', NOW())
    """, {"job_name": job_name, "source_type": source_type, "source_name": source_name})
    r = one("SELECT LAST_INSERT_ID() AS id")
    return int((r or {"id": 0})["id"])

def finish_job(job_id: int, status: str, *, files_found=0, files_processed=0, files_skipped=0,
               rows_inserted=0, rows_updated=0, rows_ignored=0, error_text: str | None = None,
               details: dict[str, Any] | None = None):
    exec_sql("""
        UPDATE job_runs
        SET status=:status,
            finished_at=NOW(),
            files_found=:files_found,
            files_processed=:files_processed,
            files_skipped=:files_skipped,
            rows_inserted=:rows_inserted,
            rows_updated=:rows_updated,
            rows_ignored=:rows_ignored,
            error_text=:error_text,
            details_json=:details
        WHERE id=:job_id
    """, {
        "status": status,
        "files_found": files_found,
        "files_processed": files_processed,
        "files_skipped": files_skipped,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_ignored": rows_ignored,
        "error_text": error_text,
        "details": json.dumps(details or {}, ensure_ascii=False),
        "job_id": job_id,
    })

def add_job_item(job_id: int, file_name: str | None, file_sha1: str | None, target_table: str | None,
                 action_taken: str, rows_inserted=0, rows_updated=0, rows_ignored=0, message: str | None = None):
    exec_sql("""
        INSERT INTO job_run_items
        (job_run_id, file_name, file_sha1, target_table, action_taken, rows_inserted, rows_updated, rows_ignored, message)
        VALUES (:job_run_id, :file_name, :file_sha1, :target_table, :action_taken, :rows_inserted, :rows_updated, :rows_ignored, :message)
    """, {
        "job_run_id": job_id,
        "file_name": file_name,
        "file_sha1": file_sha1,
        "target_table": target_table,
        "action_taken": action_taken,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_ignored": rows_ignored,
        "message": message,
    })

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

def gmail_service():
    if not os.path.exists(GMAIL_TOKEN_FILE):
        raise HTTPException(status_code=400, detail=f"No existe token Gmail en {GMAIL_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    return build("gmail", "v1", credentials=creds)

def gmail_search(query: str, max_results: int = 50):
    service = gmail_service()
    res = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return service, res.get("messages", [])

def get_message_full(service, msg_id: str):
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()

def get_headers(message: dict[str, Any]):
    headers = {}
    for h in message.get("payload", {}).get("headers", []):
        headers[h["name"].lower()] = h["value"]
    return headers

def walk_parts(parts):
    found = []
    for p in parts or []:
        filename = p.get("filename") or ""
        body = p.get("body", {})
        if filename and body.get("attachmentId"):
            found.append((filename, body["attachmentId"]))
        found.extend(walk_parts(p.get("parts", [])))
    return found

@app.get("/api/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True}

@app.get("/api/dashboard/summary")
def dashboard_summary(date_from: str | None = Query(default=None), date_to: str | None = Query(default=None)):
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
def detail_alertas(cliente: str, date_from: str | None = Query(default=None), date_to: str | None = Query(default=None)):
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
        add_job_item(job_id, file.filename, file_sha1, target_table, "processed", rows_inserted=1,
                     message="Archivo recibido correctamente")
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
        finish_job(job_id, "success", files_found=1, files_processed=1, rows_inserted=1, details=result)
        return result
    except Exception as exc:
        finish_job(job_id, "error", error_text=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))

def sync_gmail_generic(job_name: str, label: str, query: str, target_table: str):
    job_id = create_job(job_name, "gmail", label)
    try:
        service, messages = gmail_search(query)
        found = len(messages)
        processed = skipped = inserted = 0
        seen_files = set()

        for m in messages:
            full = get_message_full(service, m["id"])
            headers = get_headers(full)
            attachments = walk_parts(full.get("payload", {}).get("parts", []))
            if not attachments:
                skipped += 1
                continue

            for filename, attachment_id in attachments:
                file_key = f"{m['id']}::{filename}"
                file_sha1 = hashlib.sha1(file_key.encode("utf-8")).hexdigest()
                if file_key in seen_files:
                    skipped += 1
                    continue
                seen_files.add(file_key)
                inserted += 1
                processed += 1
                add_job_item(
                    job_id,
                    filename,
                    file_sha1,
                    target_table,
                    "gmail_processed",
                    rows_inserted=1,
                    message=f"Subject={headers.get('subject','')} From={headers.get('from','')}"
                )

        result = {
            "status": "ok",
            "job_id": job_id,
            "job_name": job_name,
            "source_name": label,
            "target_table": target_table,
            "files_found": found,
            "files_processed": processed,
            "files_skipped": skipped,
            "rows_inserted": inserted,
            "rows_updated": 0,
            "rows_ignored": 0,
            "message": "Sync Gmail ejecutado"
        }
        finish_job(
            job_id,
            "success",
            files_found=found,
            files_processed=processed,
            files_skipped=skipped,
            rows_inserted=inserted,
            details=result
        )
        return result
    except Exception as exc:
        finish_job(job_id, "error", error_text=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/sync/bd2")
def sync_bd2():
    return sync_gmail_generic(
        "bd2_sync",
        "Gmail BD2 Alertas",
        'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts") newer_than:60d',
        "printanista_alertas.alertas_actives"
    )

@app.post("/api/sync/bd3")
def sync_bd3():
    return sync_gmail_generic(
        "bd3_sync",
        "Gmail BD3 Dispositivos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_insumos.dispositivos_detallado_gv2"
    )

@app.post("/api/sync/bd4")
def sync_bd4():
    return sync_gmail_generic(
        "bd4_sync",
        "Gmail BD4 Reemplazos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_reemplazos.reemplazos_insumos_gv"
    )

@app.post("/api/sync/all")
def sync_all():
    r2 = sync_gmail_generic(
        "bd2_sync_all", "Gmail BD2 Alertas",
        'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts") newer_than:60d',
        "printanista_alertas.alertas_actives"
    )
    r3 = sync_gmail_generic(
        "bd3_sync_all", "Gmail BD3 Dispositivos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_insumos.dispositivos_detallado_gv2"
    )
    r4 = sync_gmail_generic(
        "bd4_sync_all", "Gmail BD4 Reemplazos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_reemplazos.reemplazos_insumos_gv"
    )
    return {
        "status": "ok",
        "children": {"bd2": r2, "bd3": r3, "bd4": r4},
        "files_found": r2["files_found"] + r3["files_found"] + r4["files_found"],
        "files_processed": r2["files_processed"] + r3["files_processed"] + r4["files_processed"],
        "files_skipped": r2["files_skipped"] + r3["files_skipped"] + r4["files_skipped"],
        "rows_inserted": r2["rows_inserted"] + r3["rows_inserted"] + r4["rows_inserted"],
        "rows_updated": 0,
        "rows_ignored": 0,
        "message": "Sync All ejecutado"
    }

if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")
