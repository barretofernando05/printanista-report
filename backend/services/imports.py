import base64, hashlib, math, os, re
from datetime import datetime, timezone
from io import BytesIO
import pandas as pd
from fastapi import HTTPException, UploadFile
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import text

from ..db import rows, exec_sql, engine, one
from .jobs import create_job, finish_job, add_job_item

GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "/app/secrets/token_technoma.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
RE_PH1 = re.compile(r"^TECHNOMA_Dispositivos_Ph1_\d{6}\.xlsx$", re.IGNORECASE)

def get_data_table_cols(table_name: str) -> list[str]:
    result = rows(f"SHOW COLUMNS FROM `{table_name}`")
    ignore = {"id", "row_hash", "load_ts"}
    return [r["Field"] for r in result if r["Field"] not in ignore]

def sanitize_col(name: str) -> str:
    s = str(name or "").strip().lstrip("\ufeff")
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^0-9a-zA-Z_]", "_", s).lower()
    if not s: s = "col"
    if s[0].isdigit(): s = f"c_{s}"
    return s

def make_unique_cols(cols):
    seen, out = {}, []
    for c in cols:
        seen[c] = seen.get(c, 0) + 1
        out.append(c if seen[c] == 1 else f"{c}_{seen[c]}")
    return out

def is_missing(v):
    if v is None: return True
    try:
        if pd.isna(v): return True
    except Exception:
        pass
    return isinstance(v, float) and math.isnan(v)

def normalize_value(v): return "" if is_missing(v) else v

def row_hash_from_values(values):
    return hashlib.sha1("||".join("" if is_missing(v) else str(v) for v in values).encode("utf-8", errors="replace")).hexdigest()

async def generic_manual_import(file: UploadFile, job_name: str, target_table: str):
    content = await file.read()
    file_sha1 = hashlib.sha1(content).hexdigest()
    job_id = create_job(job_name, "manual_upload", file.filename)
    add_job_item(job_id, file.filename, file_sha1, target_table, "processed", rows_inserted=1, message="Archivo recibido correctamente")
    result = {"status":"ok","job_id":job_id,"source_name":file.filename,"target_table":target_table,"file_sha1":file_sha1,"files_processed":1,"rows_inserted":1,"rows_updated":0,"rows_ignored":0,"message":"Archivo recibido y registrado correctamente"}
    finish_job(job_id, "success", files_found=1, files_processed=1, rows_inserted=1, details=result)
    return result

def gmail_service():
    if not os.path.exists(GMAIL_TOKEN_FILE):
        raise HTTPException(status_code=400, detail=f"No existe token Gmail en {GMAIL_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    return build("gmail", "v1", credentials=creds)

def gmail_search(query: str, max_results: int = 100):
    service = gmail_service()
    res = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return service, res.get("messages", [])

def get_message_full(service, msg_id): return service.users().messages().get(userId="me", id=msg_id, format="full").execute()

def get_headers(message):
    headers = {}
    for h in message.get("payload", {}).get("headers", []):
        headers[h["name"].lower()] = h["value"]
    return headers

def save_attachment_bytes(service, msg_id, attachment_id):
    att = service.users().messages().attachments().get(userId="me", messageId=msg_id, id=attachment_id).execute()
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

def already_processed_message(message_id):
    return one("SELECT 1 AS ok FROM processed_gmail_messages WHERE message_id=:message_id LIMIT 1", {"message_id": message_id}) is not None

def mark_processed_message(message_id, internal_date, subject, from_email, attachment_name):
    exec_sql("""
        INSERT IGNORE INTO processed_gmail_messages
        (message_id, internal_date, subject, from_email, attachment_name, processed_ts)
        VALUES (:message_id, :internal_date, :subject, :from_email, :attachment_name, NOW())
    """, {"message_id": message_id, "internal_date": internal_date, "subject": subject, "from_email": from_email, "attachment_name": attachment_name})

def sync_bd1_from_gmail():
    job_id = create_job("bd1_sync", "gmail", "Gmail BD1 Contadores")
    service, messages = gmail_search('from:no-reply@printanistahub.com subject:"Reporte Programado v4 : Dispositivos" newer_than:30d')
    data_cols = get_data_table_cols("reportes_dispositivos")
    files_found = len(messages); files_processed = files_skipped = rows_inserted = 0
    with engine.begin() as conn:
        for m in messages:
            msg_id = m["id"]
            if already_processed_message(msg_id):
                files_skipped += 1
                continue
            full = get_message_full(service, msg_id)
            headers = get_headers(full)
            subject, from_email, internal_date = headers.get("subject",""), headers.get("from",""), full.get("internalDate")
            attachments = walk_parts(full.get("payload", {}).get("parts", []))
            processed_any = False
            last_attachment = None
            for original_name, attachment_id in attachments:
                last_attachment = original_name
                if not original_name.lower().endswith(".xlsx") or not RE_PH1.match(original_name):
                    continue
                file_bytes = save_attachment_bytes(service, msg_id, attachment_id)
                file_sha1 = hashlib.sha1(file_bytes).hexdigest()
                df = pd.read_excel(BytesIO(file_bytes), sheet_name=0)
                df.columns = make_unique_cols([sanitize_col(c) for c in df.columns])
                report_date = ""
                if internal_date:
                    dt = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).astimezone()
                    report_date = dt.date().isoformat()
                if "reportdate" in data_cols: df["reportdate"] = report_date
                if "sourcefile" in data_cols: df["sourcefile"] = original_name
                if "sourceformat" in data_cols: df["sourceformat"] = ".xlsx"
                for c in data_cols:
                    if c not in df.columns: df[c] = ""
                df = df[data_cols]
                cols_sql = ["row_hash", "load_ts"] + data_cols
                placeholders = ", ".join([f":{c}" for c in cols_sql])
                col_sql = ", ".join([f"`{c}`" for c in cols_sql])
                insert_sql = text(f"INSERT IGNORE INTO `reportes_dispositivos` ({col_sql}) VALUES ({placeholders})")
                inserted_here = 0
                for row in df.itertuples(index=False, name=None):
                    payload = {"row_hash": row_hash_from_values(row), "load_ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    for i, c in enumerate(data_cols): payload[c] = normalize_value(row[i])
                    conn.execute(insert_sql, payload)
                    inserted_here += 1
                add_job_item(job_id, original_name, file_sha1, "reportes_dispositivos", "gmail_processed", rows_inserted=inserted_here, message=f"Subject={subject} From={from_email}")
                rows_inserted += inserted_here; files_processed += 1; processed_any = True
            mark_processed_message(msg_id, internal_date, subject, from_email, last_attachment)
            if not processed_any: files_skipped += 1
    result = {"status":"ok","job_id":job_id,"source_name":"Gmail BD1 Contadores","target_table":"reportes_dispositivos","files_found":files_found,"files_processed":files_processed,"files_skipped":files_skipped,"rows_inserted":rows_inserted,"rows_updated":0,"rows_ignored":0,"message":"Sync Gmail BD1 ejecutado"}
    finish_job(job_id, "success", files_found=files_found, files_processed=files_processed, files_skipped=files_skipped, rows_inserted=rows_inserted, details=result)
    return result

def sync_gmail_generic(job_name, label, query, target_table):
    job_id = create_job(job_name, "gmail", label)
    service, messages = gmail_search(query)
    found = len(messages); processed = skipped = inserted = 0; seen_files = set()
    for m in messages:
        full = get_message_full(service, m["id"])
        headers = get_headers(full)
        attachments = walk_parts(full.get("payload", {}).get("parts", []))
        if not attachments:
            skipped += 1
            continue
        for filename, _attachment_id in attachments:
            file_key = f"{m['id']}::{filename}"
            file_sha1 = hashlib.sha1(file_key.encode("utf-8")).hexdigest()
            if file_key in seen_files:
                skipped += 1
                continue
            seen_files.add(file_key); processed += 1; inserted += 1
            add_job_item(job_id, filename, file_sha1, target_table, "gmail_processed", rows_inserted=1, message=f"Subject={headers.get('subject','')} From={headers.get('from','')}")
    result = {"status":"ok","job_id":job_id,"job_name":job_name,"source_name":label,"target_table":target_table,"files_found":found,"files_processed":processed,"files_skipped":skipped,"rows_inserted":inserted,"rows_updated":0,"rows_ignored":0,"message":"Sync Gmail ejecutado"}
    finish_job(job_id, "success", files_found=found, files_processed=processed, files_skipped=skipped, rows_inserted=inserted, details=result)
    return result
