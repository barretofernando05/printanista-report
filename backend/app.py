import base64
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import pandas as pd
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

app = FastAPI(title="Printanista Report 7.1.3", version="7.1.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RE_PH1 = re.compile(r"^TECHNOMA_Dispositivos_Ph1_\d{6}\.xlsx$", re.IGNORECASE)


# --------------------------------------------------
# DB helpers
# --------------------------------------------------
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


# --------------------------------------------------
# Bootstrap
# --------------------------------------------------
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


def ensure_processed_gmail_messages_table() -> None:
    exec_sql("""
    CREATE TABLE IF NOT EXISTS processed_gmail_messages (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      message_id VARCHAR(128) NOT NULL,
      internal_date BIGINT NULL,
      subject TEXT NULL,
      from_email VARCHAR(255) NULL,
      attachment_name TEXT NULL,
      processed_ts DATETIME NOT NULL,
      UNIQUE KEY uq_message_id (message_id)
    )
    """)


def ensure_alertas_dashboard_view() -> None:
    exec_sql("""
    CREATE OR REPLACE VIEW printanista_alertas.vw_alertas_dashboard AS
    SELECT
      id,
      report_date,
      numero_serie_txt,
      JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Nombre_Cuenta')) AS nombre_cuenta,
      JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Fabricante')) AS fabricante,
      JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Modelo')) AS modelo,
      JSON_UNQUOTE(JSON_EXTRACT(alerta_json, '$.Número_Serie')) AS numero_serie_json,
      alerta_json
    FROM printanista_alertas.alertas_actives
    """)


@app.on_event("startup")
def startup_event():
    try:
        ensure_job_tables()
    except Exception:
        pass

    try:
        ensure_processed_gmail_messages_table()
    except Exception:
        pass

    try:
        ensure_alertas_dashboard_view()
    except Exception:
        pass


# --------------------------------------------------
# Generic helpers
# --------------------------------------------------
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


def create_job(job_name: str, source_type: str, source_name: str | None):
    exec_sql("""
        INSERT INTO job_runs (job_name, source_type, source_name, status, started_at)
        VALUES (:job_name, :source_type, :source_name, 'running', NOW())
    """, {
        "job_name": job_name,
        "source_type": source_type,
        "source_name": source_name,
    })
    r = one("SELECT LAST_INSERT_ID() AS id")
    return int((r or {"id": 0})["id"])


def finish_job(
    job_id: int,
    status: str,
    *,
    files_found: int = 0,
    files_processed: int = 0,
    files_skipped: int = 0,
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


def add_job_item(
    job_id: int,
    file_name: str | None,
    file_sha1: str | None,
    target_table: str | None,
    action_taken: str,
    rows_inserted: int = 0,
    rows_updated: int = 0,
    rows_ignored: int = 0,
    message: str | None = None,
):
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


def get_data_table_cols(table_name: str) -> list[str]:
    result = rows(f"SHOW COLUMNS FROM `{table_name}`")
    cols = [r["Field"] for r in result]
    ignore = {"id", "row_hash", "load_ts"}
    return [c for c in cols if c not in ignore]


def sanitize_col(name: str) -> str:
    s = str(name or "").strip().lstrip("\ufeff")
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^0-9a-zA-Z_]", "_", s)
    s = s.lower()
    if not s:
        s = "col"
    if s[0].isdigit():
        s = f"c_{s}"
    return s


def make_unique_cols(cols: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for c in cols:
        if c not in seen:
            seen[c] = 1
            out.append(c)
        else:
            seen[c] += 1
            out.append(f"{c}_{seen[c]}")
    return out


def is_missing(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except Exception:
        pass
    if isinstance(v, float) and math.isnan(v):
        return True
    return False


def normalize_value(v):
    return "" if is_missing(v) else v


def row_hash_from_values(values) -> str:
    joined = "||".join("" if is_missing(v) else str(v) for v in values)
    return hashlib.sha1(joined.encode("utf-8", errors="replace")).hexdigest()


def gmail_service():
    if not os.path.exists(GMAIL_TOKEN_FILE):
        raise HTTPException(status_code=400, detail=f"No existe token Gmail en {GMAIL_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    return build("gmail", "v1", credentials=creds)


def gmail_search(query: str, max_results: int = 100):
    service = gmail_service()
    res = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()
    return service, res.get("messages", [])


def get_message_full(service, msg_id: str):
    return service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()


def get_headers(message: dict[str, Any]):
    headers = {}
    for h in message.get("payload", {}).get("headers", []):
        headers[h["name"].lower()] = h["value"]
    return headers


def save_attachment_bytes(service, msg_id: str, attachment_id: str) -> bytes:
    att = service.users().messages().attachments().get(
        userId="me",
        messageId=msg_id,
        id=attachment_id,
    ).execute()
    return base64.urlsafe_b64decode(att["data"].encode("utf-8"))


def walk_parts(parts):
    found = []
    for p in parts or []:
        filename = p.get("filename") or ""
        body = p.get("body", {})
        if filename and body.get("attachmentId"):
            found.append((filename, body["attachmentId"]))
        found.extend(walk_parts(p.get("parts", [])))
    return found


def already_processed_message(message_id: str) -> bool:
    r = one(
        "SELECT 1 AS ok FROM processed_gmail_messages WHERE message_id=:message_id LIMIT 1",
        {"message_id": message_id},
    )
    return r is not None


def mark_processed_message(
    message_id: str,
    internal_date: int | None,
    subject: str | None,
    from_email: str | None,
    attachment_name: str | None,
):
    exec_sql("""
        INSERT IGNORE INTO processed_gmail_messages
        (message_id, internal_date, subject, from_email, attachment_name, processed_ts)
        VALUES (:message_id, :internal_date, :subject, :from_email, :attachment_name, NOW())
    """, {
        "message_id": message_id,
        "internal_date": internal_date,
        "subject": subject,
        "from_email": from_email,
        "attachment_name": attachment_name,
    })


# --------------------------------------------------
# Manual imports
# --------------------------------------------------
@app.post("/api/import/bd1")
async def import_bd1(file: UploadFile = File(...)):
    return await _generic_import(file, "bd1_manual", "reportes_dispositivos")


@app.post("/api/import/bd3")
async def import_bd3(file: UploadFile = File(...)):
    return await _generic_import(file, "bd3_manual", "printanista_insumos.dispositivos_detallado_gv2")


async def _generic_import(file: UploadFile, job_name: str, target_table: str):
    content = await file.read()
    file_sha1 = hashlib.sha1(content).hexdigest()
    job_id = create_job(job_name, "manual_upload", file.filename)

    try:
        add_job_item(
            job_id,
            file.filename,
            file_sha1,
            target_table,
            "processed",
            rows_inserted=1,
            message="Archivo recibido correctamente",
        )

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
            "message": "Archivo recibido y registrado correctamente",
        }

        finish_job(
            job_id,
            "success",
            files_found=1,
            files_processed=1,
            rows_inserted=1,
            details=result,
        )
        return result

    except Exception as exc:
        finish_job(job_id, "error", error_text=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


# --------------------------------------------------
# Gmail syncs
# --------------------------------------------------
def sync_bd1_from_gmail():
    job_id = create_job("bd1_sync", "gmail", "Gmail BD1 Contadores")
    try:
        service, messages = gmail_search(
            'from:no-reply@printanistahub.com subject:"Reporte Programado v4 : Dispositivos" newer_than:30d'
        )

        data_cols = get_data_table_cols("reportes_dispositivos")
        files_found = len(messages)
        files_processed = 0
        files_skipped = 0
        rows_inserted = 0

        with engine.begin() as conn:
            for m in messages:
                msg_id = m["id"]

                if already_processed_message(msg_id):
                    files_skipped += 1
                    continue

                full = get_message_full(service, msg_id)
                headers = get_headers(full)
                subject = headers.get("subject", "")
                from_email = headers.get("from", "")
                internal_date = full.get("internalDate")
                attachments = walk_parts(full.get("payload", {}).get("parts", []))

                if not attachments:
                    mark_processed_message(msg_id, internal_date, subject, from_email, None)
                    files_skipped += 1
                    continue

                processed_any_attachment = False

                for original_name, attachment_id in attachments:
                    if not original_name.lower().endswith(".xlsx"):
                        continue

                    if not RE_PH1.match(original_name):
                        files_skipped += 1
                        continue

                    file_bytes = save_attachment_bytes(service, msg_id, attachment_id)
                    file_sha1 = hashlib.sha1(file_bytes).hexdigest()

                    df = pd.read_excel(BytesIO(file_bytes), sheet_name=0)
                    df.columns = make_unique_cols([sanitize_col(c) for c in df.columns])

                    report_date = ""
                    if internal_date:
                        dt = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).astimezone()
                        report_date = dt.date().isoformat()

                    if "reportdate" in data_cols:
                        df["reportdate"] = report_date
                    if "sourcefile" in data_cols:
                        df["sourcefile"] = original_name
                    if "sourceformat" in data_cols:
                        df["sourceformat"] = ".xlsx"

                    for c in data_cols:
                        if c not in df.columns:
                            df[c] = ""

                    df = df[data_cols]
                    load_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    inserted_here = 0

                    cols_sql = ["row_hash", "load_ts"] + data_cols
                    placeholders = ", ".join([f":{c}" for c in cols_sql])
                    col_sql = ", ".join([f"`{c}`" for c in cols_sql])
                    insert_sql = text(f"INSERT IGNORE INTO `reportes_dispositivos` ({col_sql}) VALUES ({placeholders})")

                    for row in df.itertuples(index=False, name=None):
                        rh = row_hash_from_values(row)
                        payload = {"row_hash": rh, "load_ts": load_ts}
                        for i, c in enumerate(data_cols):
                            payload[c] = normalize_value(row[i])

                        conn.execute(insert_sql, payload)
                        inserted_here += 1

                    add_job_item(
                        job_id,
                        original_name,
                        file_sha1,
                        "reportes_dispositivos",
                        "gmail_processed",
                        rows_inserted=inserted_here,
                        message=f"Subject={subject} From={from_email}",
                    )

                    rows_inserted += inserted_here
                    files_processed += 1
                    processed_any_attachment = True

                mark_processed_message(
                    msg_id,
                    internal_date,
                    subject,
                    from_email,
                    original_name if attachments else None,
                )

                if not processed_any_attachment:
                    files_skipped += 1

        result = {
            "status": "ok",
            "job_id": job_id,
            "source_name": "Gmail BD1 Contadores",
            "target_table": "reportes_dispositivos",
            "files_found": files_found,
            "files_processed": files_processed,
            "files_skipped": files_skipped,
            "rows_inserted": rows_inserted,
            "rows_updated": 0,
            "rows_ignored": 0,
            "message": "Sync Gmail BD1 ejecutado",
        }

        finish_job(
            job_id,
            "success",
            files_found=files_found,
            files_processed=files_processed,
            files_skipped=files_skipped,
            rows_inserted=rows_inserted,
            details=result,
        )
        return result

    except Exception as exc:
        finish_job(job_id, "error", error_text=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


def sync_gmail_generic(job_name: str, label: str, query: str, target_table: str):
    job_id = create_job(job_name, "gmail", label)

    try:
        service, messages = gmail_search(query)
        found = len(messages)
        processed = 0
        skipped = 0
        inserted = 0
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
                processed += 1
                inserted += 1

                add_job_item(
                    job_id,
                    filename,
                    file_sha1,
                    target_table,
                    "gmail_processed",
                    rows_inserted=1,
                    message=f"Subject={headers.get('subject', '')} From={headers.get('from', '')}",
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
            "message": "Sync Gmail ejecutado",
        }

        finish_job(
            job_id,
            "success",
            files_found=found,
            files_processed=processed,
            files_skipped=skipped,
            rows_inserted=inserted,
            details=result,
        )
        return result

    except Exception as exc:
        finish_job(job_id, "error", error_text=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/sync/bd1")
def sync_bd1():
    return sync_bd1_from_gmail()


@app.post("/api/sync/bd2")
def sync_bd2():
    return sync_gmail_generic(
        "bd2_sync",
        "Gmail BD2 Alertas",
        'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts") newer_than:60d',
        "printanista_alertas.alertas_actives",
    )


@app.post("/api/sync/bd3")
def sync_bd3():
    return sync_gmail_generic(
        "bd3_sync",
        "Gmail BD3 Dispositivos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_insumos.dispositivos_detallado_gv2",
    )


@app.post("/api/sync/bd4")
def sync_bd4():
    return sync_gmail_generic(
        "bd4_sync",
        "Gmail BD4 Reemplazos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_reemplazos.reemplazos_insumos_gv",
    )


@app.post("/api/sync/all")
def sync_all():
    r1 = sync_bd1_from_gmail()
    r2 = sync_gmail_generic(
        "bd2_sync_all",
        "Gmail BD2 Alertas",
        'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts") newer_than:60d',
        "printanista_alertas.alertas_actives",
    )
    r3 = sync_gmail_generic(
        "bd3_sync_all",
        "Gmail BD3 Dispositivos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_insumos.dispositivos_detallado_gv2",
    )
    r4 = sync_gmail_generic(
        "bd4_sync_all",
        "Gmail BD4 Reemplazos",
        'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d',
        "printanista_reemplazos.reemplazos_insumos_gv",
    )

    return {
        "status": "ok",
        "children": {"bd1": r1, "bd2": r2, "bd3": r3, "bd4": r4},
        "files_found": r1["files_found"] + r2["files_found"] + r3["files_found"] + r4["files_found"],
        "files_processed": r1["files_processed"] + r2["files_processed"] + r3["files_processed"] + r4["files_processed"],
        "files_skipped": r1["files_skipped"] + r2["files_skipped"] + r3["files_skipped"] + r4["files_skipped"],
        "rows_inserted": r1["rows_inserted"] + r2["rows_inserted"] + r3["rows_inserted"] + r4["rows_inserted"],
        "rows_updated": 0,
        "rows_ignored": 0,
        "message": "Sync All ejecutado",
    }


# --------------------------------------------------
# Dashboard / query APIs
# --------------------------------------------------
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
        SELECT COUNT(DISTINCT numero_serie_txt) AS total
        FROM printanista_alertas.alertas_actives
        WHERE {where}
    """, params)

    clientes = safe_rows(f"""
        SELECT COALESCE(nombre_cuenta, 'SIN CLIENTE') AS name, COUNT(*) AS total
        FROM printanista_alertas.vw_alertas_dashboard
        WHERE {where}
        GROUP BY nombre_cuenta
        ORDER BY total DESC
        LIMIT 10
    """, params)

    modelos = safe_rows(f"""
        SELECT COALESCE(modelo, 'SIN MODELO') AS name, COUNT(*) AS total
        FROM printanista_alertas.vw_alertas_dashboard
        WHERE {where} AND COALESCE(fabricante, '') = 'RICOH'
        GROUP BY modelo
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

    reemplazos_mes = safe_rows("""
        SELECT DATE_FORMAT(report_date, '%Y-%m') AS name, COUNT(*) AS total
        FROM printanista_reemplazos.reemplazos_insumos_gv
        WHERE report_date IS NOT NULL
        GROUP BY DATE_FORMAT(report_date, '%Y-%m')
        ORDER BY name
    """)

    equipos_modelo = safe_rows("""
        SELECT COALESCE(modelo, 'SIN MODELO') AS name, COUNT(*) AS total
        FROM printanista_insumos.dispositivos_detallado_gv2
        GROUP BY modelo
        ORDER BY total DESC
        LIMIT 10
    """)

    return {
        "kpis": {
            "equipos_monitoreados": equipos,
            "alertas_activas": safe_count(
                f"SELECT COUNT(*) AS total FROM printanista_alertas.alertas_actives WHERE {where}",
                params,
            ),
            "reemplazos": safe_count(
                f"SELECT COUNT(*) AS total FROM printanista_reemplazos.reemplazos_insumos_gv WHERE {where}",
                params,
            ),
            "porc_equipos_con_alertas": round((equipos_alerta / equipos) * 100, 2) if equipos else 0,
        },
        "clientes": clientes,
        "modelos": modelos,
        "timeline": timeline,
        "reemplazos_mes": reemplazos_mes,
        "equipos_modelo": equipos_modelo,
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
        SELECT
          id,
          report_date,
          numero_serie_txt,
          nombre_cuenta,
          fabricante,
          modelo,
          numero_serie_json,
          alerta_json
        FROM printanista_alertas.vw_alertas_dashboard
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


# --------------------------------------------------
# Frontend at root
# --------------------------------------------------
if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")