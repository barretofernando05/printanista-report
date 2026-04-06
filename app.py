
import base64
import hashlib
import io
import json
import math
import os
import re
import unicodedata
from datetime import date, datetime
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "printanista")
DB_USER = os.getenv("DB_USER", "printanista")
DB_PASSWORD = os.getenv("DB_PASSWORD", "printanista123")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "/app/secrets/token_technoma.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="Printanista Report V4", version="4.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- general helpers ----------------

def rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with engine.begin() as conn:
        return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]

def one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {}).mappings().first()
        return dict(result) if result else None

def exec_sql(sql: str, params: dict[str, Any] | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

def get_columns(schema: str, table: str) -> set[str]:
    sql = """
    SELECT COLUMN_NAME
    FROM information_schema.columns
    WHERE table_schema = :schema
      AND table_name = :table
    """
    with engine.begin() as conn:
        return {r[0] for r in conn.execute(text(sql), {"schema": schema, "table": table}).all()}

def pick_first(columns: set[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in columns:
            return c
    return None

def build_where(columns: set[str], candidates: list[str], param_name: str = "serie") -> str:
    col = pick_first(columns, candidates)
    if not col:
        return "1=0"
    return f"`{col}` = :{param_name}"

def safe_count(sql: str, params: dict[str, Any] | None = None) -> int:
    try:
        r = one(sql, params)
        return int(r["total"]) if r and r.get("total") is not None else 0
    except Exception:
        return 0

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

# ---------------- text helpers ----------------

def strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def sanitize_col(name) -> str:
    name = strip_accents(str(name).strip().lstrip("\ufeff"))
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    name = name.lower()
    if not name:
        name = "col"
    if name[0].isdigit():
        name = "c_" + name
    return name

def safe_str(x: Any) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x)

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

def normalize_serie(x: Any) -> str | None:
    s = safe_str(x).strip()
    return None if s == "" or s.upper() == "NULL" else s

def normalize_ip(x: Any) -> str | None:
    s = safe_str(x).strip()
    return None if s == "" else s

def normalize_counter(x: Any) -> int | None:
    try:
        v = pd.to_numeric(x, errors="coerce")
        if pd.isna(v):
            return None
        return int(v)
    except Exception:
        return None

def normalize_audit_datetime(x: Any) -> str | None:
    try:
        ts = pd.to_datetime(x, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def extract_reportdate_from_filename(filename: str) -> str | None:
    m = re.search(r"(\d{6})(?=\.(xlsx|csv)$)", filename, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%y%m%d").date().isoformat()
    except Exception:
        return None

def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()

def row_hash_from_values(values) -> str:
    joined = "||".join("" if is_missing(v) else str(v) for v in values)
    return hashlib.sha1(joined.encode("utf-8", errors="replace")).hexdigest()

# ---------------- gmail helpers ----------------

def gmail_service():
    if not os.path.exists(GMAIL_TOKEN_FILE):
        raise HTTPException(status_code=400, detail=f"No existe token Gmail en {GMAIL_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    return build("gmail", "v1", credentials=creds)

def gmail_search(service, query: str, max_results=100):
    res = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return res.get("messages", [])

def get_message_full(service, msg_id: str):
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()

def save_attachment(service, msg_id: str, attachment_id: str) -> bytes:
    res = service.users().messages().attachments().get(userId="me", messageId=msg_id, id=attachment_id).execute()
    data = res.get("data", "")
    return base64.urlsafe_b64decode(data.encode("utf-8"))

def extract_attachments(service, full, ext=".xlsx"):
    found = []
    def walk(parts):
        for p in parts or []:
            filename = p.get("filename", "")
            body = p.get("body", {})
            if filename.lower().endswith(ext) and body.get("attachmentId"):
                found.append((filename, body["attachmentId"]))
            walk(p.get("parts", []))
    payload = full.get("payload", {})
    walk(payload.get("parts", []))
    return found

def json_dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)

# ---------------- import BD1 manual ----------------

def load_bd1_manual(file_bytes: bytes, sourcefile: str, sheet_name: str = "Reporte") -> dict[str, Any]:
    file_sha1 = sha1_bytes(file_bytes)
    already = one("SELECT COUNT(*) AS n FROM printanista.processed_files_bd1 WHERE file_sha1=:s", {"s": file_sha1})
    if already and already["n"] > 0:
        return {"status": "skipped", "message": "Archivo ya procesado por SHA1", "file_sha1": file_sha1}

    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    col_map = {
        "Es Administrado": "es_administrado",
        "Nombre Cuenta": "nombre_cuenta",
        "Fabricante": "fabricante",
        "Modelo": "modelo",
        "Número Serie": "n_mero_serie",
        "Total páginas mono": "total_p_ginas_mono",
        "Total Páginas Color": "total_p_ginas_color",
        "Dirección IP": "direcci_n_ip",
        "Última Fecha Auditoría Medidores": "_ltima_fecha_auditor_a_medidores",
    }
    out = pd.DataFrame()
    for excel_col, db_col in col_map.items():
        out[db_col] = df[excel_col] if excel_col in df.columns else None

    out["n_mero_serie"] = out["n_mero_serie"].apply(normalize_serie)
    out["direcci_n_ip"] = out["direcci_n_ip"].apply(normalize_ip)
    out["total_p_ginas_mono"] = out["total_p_ginas_mono"].apply(normalize_counter)
    out["total_p_ginas_color"] = out["total_p_ginas_color"].apply(normalize_counter)
    out["_ltima_fecha_auditor_a_medidores"] = out["_ltima_fecha_auditor_a_medidores"].apply(normalize_audit_datetime)

    load_ts = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    reportdate = extract_reportdate_from_filename(sourcefile)
    out["load_ts"] = load_ts
    out["sourcefile"] = sourcefile
    out["sourceformat"] = "xlsx"
    out["reportdate"] = reportdate
    out["row_hash"] = out.apply(
        lambda r: hashlib.sha1("||".join([
            safe_str(sourcefile),
            safe_str(normalize_serie(r.get("n_mero_serie"))),
            safe_str(normalize_counter(r.get("total_p_ginas_mono"))),
            safe_str(normalize_counter(r.get("total_p_ginas_color"))),
            safe_str(normalize_ip(r.get("direcci_n_ip"))),
            safe_str(normalize_audit_datetime(r.get("_ltima_fecha_auditor_a_medidores"))),
        ]).encode("utf-8")).hexdigest(),
        axis=1,
    )

    cols = [
        "row_hash","load_ts","es_administrado","nombre_cuenta","fabricante","modelo","n_mero_serie",
        "total_p_ginas_mono","total_p_ginas_color","direcci_n_ip","_ltima_fecha_auditor_a_medidores",
        "reportdate","sourcefile","sourceformat"
    ]
    out = out[cols].astype(object).where(pd.notnull(out), None)
    insert_sql = """
    INSERT INTO printanista.reportes_dispositivos
    (`row_hash`,`load_ts`,`es_administrado`,`nombre_cuenta`,`fabricante`,`modelo`,`n_mero_serie`,
     `total_p_ginas_mono`,`total_p_ginas_color`,`direcci_n_ip`,`_ltima_fecha_auditor_a_medidores`,
     `reportdate`,`sourcefile`,`sourceformat`)
    VALUES (:row_hash,:load_ts,:es_administrado,:nombre_cuenta,:fabricante,:modelo,:n_mero_serie,
            :total_p_ginas_mono,:total_p_ginas_color,:direcci_n_ip,:_ltima_fecha_auditor_a_medidores,
            :reportdate,:sourcefile,:sourceformat)
    ON DUPLICATE KEY UPDATE
      load_ts=VALUES(load_ts),
      sourcefile=VALUES(sourcefile),
      sourceformat=VALUES(sourceformat),
      reportdate=VALUES(reportdate),
      es_administrado=VALUES(es_administrado),
      nombre_cuenta=VALUES(nombre_cuenta),
      fabricante=VALUES(fabricante),
      modelo=VALUES(modelo),
      n_mero_serie=VALUES(n_mero_serie),
      total_p_ginas_mono=VALUES(total_p_ginas_mono),
      total_p_ginas_color=VALUES(total_p_ginas_color),
      direcci_n_ip=VALUES(direcci_n_ip),
      _ltima_fecha_auditor_a_medidores=VALUES(_ltima_fecha_auditor_a_medidores)
    """
    with engine.begin() as conn:
        for record in out.to_dict(orient="records"):
            conn.execute(text(insert_sql), record)
        conn.execute(text("""
            INSERT IGNORE INTO printanista.processed_files_bd1 (file_sha1, sourcefile, processed_ts)
            VALUES (:s,:f,NOW())
        """), {"s": file_sha1, "f": sourcefile})
    return {"status": "ok", "rows": len(out), "file_sha1": file_sha1, "reportdate": reportdate}

# ---------------- import BD3 manual ----------------

EXCEL_TO_DB_BD3 = {
    "nombre cuenta": "nombre_cuenta",
    "fabricante": "fabricante",
    "modelo": "modelo",
    "numero serie": "numero_serie",
    "n° serie": "numero_serie",
    "dirección ip": "direccion_ip",
    "direccion ip": "direccion_ip",
    "numero activo": "numero_activo",
    "id erp": "id_erp",
    "ubicacion": "ubicacion",
    "total paginas mono": "total_paginas_mono",
    "total páginas mono": "total_paginas_mono",
    "total paginas color": "total_paginas_color",
    "total páginas color": "total_paginas_color",
    "volumen mensual medio": "volumen_mensual_medio",
    "amv mono": "amv_mono",
    "amv color": "amv_color",
    "nombre suministro": "nombre_suministro",
    "% nivel": "nivel",
    "cobertura%": "cobertura",
    "nro pieza": "no_pieza",
    "nº pieza": "no_pieza",
    "rendimiento": "rendimiento",
    "fecha estimada de vacio": "fecha_estimada_de_vacio",
    "primera fecha auditoria": "primera_fecha_auditoria",
    "fecha ultima auditoria": "fecha_ultima_auditoria",
    "copias servicio totales": "copias_servicio_totales",
    "historial servicio": "historial_servicio",
    "contacto de servicio": "contacto_de_servicio",
    "total llamadas de servicio": "total_llamadas_de_servicio",
    "ultimo servicio": "ultimo_servicio",
    "intervalo mantenimiento preventivo": "intervalo_mantenimiento_preventivo",
    "paginas hasta mantenimiento preventivo": "paginas_hasta_mantenimiento_preventivo",
    "alertas dispositivo": "alertas_dispositivo",
}

def norm_col(c: str) -> str:
    c = strip_accents(str(c).strip().lower()).replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", c)

def load_bd3_manual(file_bytes: bytes, sourcefile: str) -> dict[str, Any]:
    file_sha1 = sha1_bytes(file_bytes)
    already = one("SELECT COUNT(*) AS n FROM printanista_insumos.processed_files_bd3 WHERE file_sha1=:s", {"s": file_sha1})
    if already and already["n"] > 0:
        return {"status": "skipped", "message": "Archivo ya procesado por SHA1", "file_sha1": file_sha1}

    report_dt = extract_reportdate_from_filename(sourcefile)
    if not report_dt:
        raise HTTPException(status_code=400, detail="No pude detectar fecha YYMMDD en el nombre del archivo BD3.")

    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheet = xls.sheet_names[0] if xls.sheet_names else "Reporte"
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet)
    df.columns = [norm_col(c) for c in df.columns]

    db_cols = [
        "row_hash","load_ts","report_date","sourcefile","sheet_name","sourceformat","nombre_cuenta","fabricante","modelo",
        "numero_serie","direccion_ip","numero_activo","id_erp","ubicacion","total_paginas_mono","total_paginas_color",
        "volumen_mensual_medio","amv_mono","amv_color","nombre_suministro","nivel","cobertura","no_pieza","rendimiento",
        "fecha_estimada_de_vacio","primera_fecha_auditoria","fecha_ultima_auditoria","copias_servicio_totales",
        "historial_servicio","contacto_de_servicio","total_llamadas_de_servicio","ultimo_servicio",
        "intervalo_mantenimiento_preventivo","paginas_hasta_mantenimiento_preventivo","alertas_dispositivo",
        "numero_serie_idx","report_date_idx"
    ]

    prepared = []
    load_ts = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    for _, r in df.iterrows():
        out = {c: "" for c in db_cols}
        out["load_ts"] = load_ts
        out["report_date"] = report_dt
        out["report_date_idx"] = report_dt
        out["sourcefile"] = sourcefile
        out["sheet_name"] = sheet
        out["sourceformat"] = ".xlsx"

        for excel_col_norm, db_col in EXCEL_TO_DB_BD3.items():
            if excel_col_norm in df.columns:
                out[db_col] = safe_str(r.get(excel_col_norm))

        serie = safe_str(out.get("numero_serie")).strip()
        out["numero_serie"] = serie
        out["numero_serie_idx"] = serie
        hash_fields = [
            report_dt, sourcefile, sheet, out.get("numero_serie",""), out.get("modelo",""), out.get("fabricante",""),
            out.get("nombre_suministro",""), out.get("nivel",""), out.get("cobertura",""), out.get("no_pieza",""),
            out.get("rendimiento",""), out.get("ubicacion",""), out.get("direccion_ip","")
        ]
        out["row_hash"] = hashlib.sha1("||".join(hash_fields).encode("utf-8")).hexdigest()
        prepared.append(out)

    cols_sql = ", ".join([f"`{c}`" for c in db_cols])
    values_sql = ", ".join([f":{c}" for c in db_cols])
    upd_cols = [c for c in db_cols if c != "row_hash"]
    upd_sql = ", ".join([f"`{c}`=VALUES(`{c}`)" for c in upd_cols])
    sql = f"""
    INSERT INTO printanista_insumos.dispositivos_detallado_gv2 ({cols_sql})
    VALUES ({values_sql})
    ON DUPLICATE KEY UPDATE {upd_sql}
    """
    with engine.begin() as conn:
        for rec in prepared:
            conn.execute(text(sql), rec)
        conn.execute(text("""
            INSERT IGNORE INTO printanista_insumos.processed_files_bd3 (file_sha1, sourcefile, processed_ts)
            VALUES (:s,:f,NOW())
        """), {"s": file_sha1, "f": sourcefile})
    return {"status": "ok", "rows": len(prepared), "file_sha1": file_sha1, "reportdate": report_dt}

# ---------------- gmail syncs ----------------

def sync_bd2_alertas(max_results: int = 100) -> dict[str, Any]:
    service = gmail_service()
    query = 'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts" OR subject:"Alerts") newer_than:30d'
    msgs = gmail_search(service, query=query, max_results=max_results)
    processed = skipped = rows_inserted = 0

    alertas_cols = get_columns("printanista_alertas", "alertas_actives")
    json_col = pick_first(alertas_cols, ["alerta_json", "json_payload", "raw_json"])
    serie_col = pick_first(alertas_cols, ["numero_serie_txt", "numero_serie", "serial", "serie"])
    date_col = pick_first(alertas_cols, ["report_date", "fecha", "reportdate"])
    file_col = pick_first(alertas_cols, ["sourcefile"])
    sheet_col = pick_first(alertas_cols, ["sheet_name"])
    rowhash_col = pick_first(alertas_cols, ["row_hash"])
    load_col = pick_first(alertas_cols, ["load_ts"])

    if not rowhash_col:
        raise HTTPException(status_code=500, detail="La tabla alertas_actives no tiene row_hash.")

    for m in msgs:
        full = get_message_full(service, m["id"])
        attachments = extract_attachments(service, full, ".xlsx")
        for filename, attachment_id in attachments:
            if re.match(r"^TECHNOMA_Alertas_Active Alerts_(\d{6})\.xlsx$", filename, flags=re.IGNORECASE) is None:
                continue
            data = save_attachment(service, m["id"], attachment_id)
            fsha1 = sha1_bytes(data)
            already = one("SELECT COUNT(*) AS n FROM printanista_alertas.processed_files_bd2 WHERE file_sha1=:s", {"s": fsha1})
            if already and already["n"] > 0:
                skipped += 1
                continue
            report_date = extract_reportdate_from_filename(filename)
            df = pd.read_excel(io.BytesIO(data), sheet_name=0)
            inserted_here = 0
            with engine.begin() as conn:
                for _, row in df.iterrows():
                    payload = {str(k): (None if pd.isna(v) else str(v)) for k, v in row.to_dict().items()}
                    serie_value = payload.get("Número Serie") or payload.get("Numero Serie") or payload.get("numero_serie")
                    rec = {
                        rowhash_col: hashlib.sha1(json_dumps(payload).encode("utf-8")).hexdigest()
                    }
                    if load_col:
                        rec[load_col] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if date_col:
                        rec[date_col] = report_date
                    if file_col:
                        rec[file_col] = filename
                    if sheet_col:
                        rec[sheet_col] = "sheet1"
                    if json_col:
                        rec[json_col] = json_dumps(payload)
                    if serie_col:
                        rec[serie_col] = serie_value

                    cols = ", ".join(f"`{k}`" for k in rec.keys())
                    vals = ", ".join(f":{k}" for k in rec.keys())
                    conn.execute(text(f"INSERT IGNORE INTO printanista_alertas.alertas_actives ({cols}) VALUES ({vals})"), rec)
                    inserted_here += 1
                conn.execute(text("""
                    INSERT IGNORE INTO printanista_alertas.processed_files_bd2 (file_sha1, sourcefile, processed_ts)
                    VALUES (:s,:f,NOW())
                """), {"s": fsha1, "f": filename})
            processed += 1
            rows_inserted += inserted_here
    return {"status": "ok", "files_processed": processed, "files_skipped": skipped, "rows_attempted": rows_inserted}

def sync_bd3_insumos(max_results: int = 100) -> dict[str, Any]:
    service = gmail_service()
    query = 'from:no-reply@printanistahub.com subject:"Reporte Programado v4" has:attachment filename:xlsx newer_than:60d'
    msgs = gmail_search(service, query=query, max_results=max_results)
    data_cols = [c for c in get_columns("printanista_insumos", "dispositivos_detallado_gv2") if c not in {"id"}]
    processed = skipped = rows_attempted = 0

    for m in msgs:
        full = get_message_full(service, m["id"])
        attachments = extract_attachments(service, full, ".xlsx")
        for filename, attachment_id in attachments:
            if re.match(r"^TECHNOMA_Dispositivos_Dispositivos_Detallado_GV2_(\d{6})\.xlsx$", filename, flags=re.IGNORECASE) is None:
                continue
            data = save_attachment(service, m["id"], attachment_id)
            fsha1 = sha1_bytes(data)
            already = one("SELECT COUNT(*) AS n FROM printanista_insumos.processed_files_bd3 WHERE file_sha1=:s", {"s": fsha1})
            if already and already["n"] > 0:
                skipped += 1
                continue

            df = pd.read_excel(io.BytesIO(data), sheet_name=0)
            df.columns = [sanitize_col(c) for c in df.columns]
            reportdate = extract_reportdate_from_filename(filename)
            if "report_date" in data_cols:
                df["report_date"] = reportdate or None
            if "report_date_idx" in data_cols:
                df["report_date_idx"] = reportdate or None
            if "sourcefile" in data_cols:
                df["sourcefile"] = filename
            if "sheet_name" in data_cols:
                df["sheet_name"] = "sheet1"
            if "sourceformat" in data_cols:
                df["sourceformat"] = ".xlsx"
            if "numero_serie_idx" in data_cols:
                df["numero_serie_idx"] = df["numero_serie"].apply(lambda v: "" if is_missing(v) else str(v).strip()) if "numero_serie" in df.columns else ""
            if "load_ts" in data_cols:
                df["load_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for c in data_cols:
                if c not in df.columns:
                    df[c] = None
            base_cols = [c for c in data_cols if c != "row_hash"]
            cols_sql = ["row_hash"] + base_cols
            cols_stmt = ", ".join(f"`{c}`" for c in cols_sql)
            vals_stmt = ", ".join(f":{c}" for c in cols_sql)
            upd_stmt = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in cols_sql if c != "row_hash")
            sql = f"INSERT INTO printanista_insumos.dispositivos_detallado_gv2 ({cols_stmt}) VALUES ({vals_stmt}) ON DUPLICATE KEY UPDATE {upd_stmt}"

            with engine.begin() as conn:
                for _, row in df.iterrows():
                    rec = {}
                    values_for_hash = []
                    for c in base_cols:
                        v = row[c]
                        rec[c] = None if is_missing(v) else v
                        values_for_hash.append(rec[c])
                    rec["row_hash"] = row_hash_from_values(values_for_hash)
                    conn.execute(text(sql), rec)
                    rows_attempted += 1
                conn.execute(text("""
                    INSERT IGNORE INTO printanista_insumos.processed_files_bd3 (file_sha1, sourcefile, processed_ts)
                    VALUES (:s,:f,NOW())
                """), {"s": fsha1, "f": filename})
            processed += 1
    return {"status": "ok", "files_processed": processed, "files_skipped": skipped, "rows_attempted": rows_attempted}

def sync_bd4_reemplazos(max_results: int = 100) -> dict[str, Any]:
    service = gmail_service()
    query = 'from:no-reply@printanistahub.com subject:"Reporte Programado v4" has:attachment filename:xlsx newer_than:60d'
    msgs = gmail_search(service, query=query, max_results=max_results)
    data_cols = [c for c in get_columns("printanista_reemplazos", "reemplazos_insumos_gv") if c not in {"id"}]
    processed = skipped = rows_attempted = 0

    header_map = {
        "Nombre Cuenta":"nombre_cuenta","Fabricante":"fabricante","Modelo":"modelo","Numero Serie":"numero_serie",
        "ID ERP":"id_erp","Suministro":"suministro","# Parte OEM":"parte_oem","Rendimiento":"rendimiento",
        "Numero de Serie del Suministro":"numero_de_serie_del_suministro","Fecha Instalacion":"fecha_instalacion",
        "Contador Instalacion":"contador_instalacion","Nivel Instalacion":"nivel_instalacion","Fecha de Reemplazo":"fecha_de_reemplazo",
        "Contador al Reemplazo":"contador_al_reemplazo","Nivel al Reemplazo":"nivel_al_reemplazo","Rendimiento objetivo":"rendimiento_objetivo",
        "Rendimiento Alcanzado":"rendimiento_alcanzado","Cobertura Alcanzada":"cobertura_alcanzada","Nuevo Nivel Suministro":"nuevo_nivel_suministro",
        "Nivel Mas Reciente":"nivel_mas_reciente","Fecha Est de Vacio":"fecha_est_de_vacio","Proveedor de Cartuchos":"proveedor_de_cartuchos",
    }

    for m in msgs:
        full = get_message_full(service, m["id"])
        attachments = extract_attachments(service, full, ".xlsx")
        for filename, attachment_id in attachments:
            if re.match(r"^TECHNOMA_Reemplazo de Suministro_Reemplazos_Insumos_GV_(\d{6})\.xlsx$", filename, flags=re.IGNORECASE) is None:
                continue
            data = save_attachment(service, m["id"], attachment_id)
            fsha1 = sha1_bytes(data)
            already = one("SELECT COUNT(*) AS n FROM printanista_reemplazos.processed_files_bd4 WHERE file_sha1=:s", {"s": fsha1})
            if already and already["n"] > 0:
                skipped += 1
                continue

            df = pd.read_excel(io.BytesIO(data), sheet_name=0)
            mapped = []
            for c in df.columns:
                c0 = strip_accents(str(c).strip())
                mapped.append(header_map.get(c0, sanitize_col(c0)))
            df.columns = mapped

            reportdate = extract_reportdate_from_filename(filename)
            if "report_date" in data_cols:
                df["report_date"] = reportdate or None
            if "sourcefile" in data_cols:
                df["sourcefile"] = filename
            if "sheet_name" in data_cols:
                df["sheet_name"] = "Reporte"
            if "sourceformat" in data_cols:
                df["sourceformat"] = ".xlsx"
            if "numero_serie_idx" in data_cols:
                df["numero_serie_idx"] = df["numero_serie"].apply(lambda v: "" if is_missing(v) else str(v).strip()) if "numero_serie" in df.columns else ""
            if "load_ts" in data_cols:
                df["load_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for c in data_cols:
                if c not in df.columns:
                    df[c] = None

            base_cols = [c for c in data_cols if c != "row_hash"]
            cols_sql = ["row_hash"] + base_cols
            cols_stmt = ", ".join(f"`{c}`" for c in cols_sql)
            vals_stmt = ", ".join(f":{c}" for c in cols_sql)
            sql = f"INSERT IGNORE INTO printanista_reemplazos.reemplazos_insumos_gv ({cols_stmt}) VALUES ({vals_stmt})"

            with engine.begin() as conn:
                for _, row in df.iterrows():
                    rec = {}
                    values_for_hash = []
                    for c in base_cols:
                        v = row[c]
                        rec[c] = None if is_missing(v) else v
                        values_for_hash.append(rec[c])
                    rec["row_hash"] = row_hash_from_values(values_for_hash)
                    conn.execute(text(sql), rec)
                    rows_attempted += 1
                conn.execute(text("""
                    INSERT IGNORE INTO printanista_reemplazos.processed_files_bd4 (file_sha1, sourcefile, processed_ts)
                    VALUES (:s,:f,NOW())
                """), {"s": fsha1, "f": filename})
            processed += 1
    return {"status": "ok", "files_processed": processed, "files_skipped": skipped, "rows_attempted": rows_attempted}

# ---------------- query endpoints ----------------

@app.get("/api/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/api/debug/tables")
def debug_tables():
    return rows("""
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema IN ('printanista','printanista_alertas','printanista_insumos','printanista_reemplazos')
        ORDER BY table_schema, table_name
    """)

@app.get("/api/debug/columns")
def debug_columns():
    targets = [
        ("printanista_insumos", "vw_equipo_insumos_con_alertas"),
        ("printanista_insumos", "vw_equipo_insumos_resumen"),
        ("printanista_insumos", "vw_equipo_insumos_detalle"),
        ("printanista_alertas", "vw_alertas_actives"),
        ("printanista_reemplazos", "vw_reemplazos_insumos_pct"),
        ("printanista", "reportes_dispositivos"),
    ]
    return {f"{s}.{t}": sorted(get_columns(s, t)) for s, t in targets}

@app.get("/api/equipo/{serie}")
def consultar_equipo(serie: str):
    resumen_cols = get_columns("printanista_insumos", "vw_equipo_insumos_con_alertas")
    resumen = safe_one(f"""
        SELECT * FROM printanista_insumos.vw_equipo_insumos_con_alertas
        WHERE {build_where(resumen_cols, ["numero_serie","numero_serie_idx","n_mero_serie","serial","serie"])}
        LIMIT 1
    """, {"serie": serie})
    if not resumen:
        resumen_cols = get_columns("printanista_insumos", "vw_equipo_insumos_resumen")
        resumen = safe_one(f"""
            SELECT * FROM printanista_insumos.vw_equipo_insumos_resumen
            WHERE {build_where(resumen_cols, ["numero_serie","numero_serie_idx","n_mero_serie","serial","serie"])}
            LIMIT 1
        """, {"serie": serie})
    if not resumen:
        raise HTTPException(status_code=404, detail="No se encontró el equipo.")

    serie_val = resumen.get("numero_serie") or resumen.get("numero_serie_idx") or resumen.get("n_mero_serie") or resumen.get("serial") or resumen.get("serie") or serie
    detalle_cols = get_columns("printanista_insumos", "vw_equipo_insumos_detalle")
    alertas_cols = get_columns("printanista_alertas", "vw_alertas_actives")
    reemplazos_cols = get_columns("printanista_reemplazos", "vw_reemplazos_insumos_pct")
    cont_cols = get_columns("printanista", "reportes_dispositivos")

    insumos = safe_rows(f"""
        SELECT * FROM printanista_insumos.vw_equipo_insumos_detalle
        WHERE {build_where(detalle_cols, ["numero_serie","numero_serie_idx","n_mero_serie","serial","serie"], "serie_val")}
        LIMIT 200
    """, {"serie_val": serie_val})
    alertas = safe_rows(f"""
        SELECT * FROM printanista_alertas.vw_alertas_actives
        WHERE {build_where(alertas_cols, ["numero_serie","numero_serie_idx","numero_serie_txt","n_mero_serie","serial","serie"], "serie_val")}
        LIMIT 200
    """, {"serie_val": serie_val})
    reemplazos = safe_rows(f"""
        SELECT * FROM printanista_reemplazos.vw_reemplazos_insumos_pct
        WHERE {build_where(reemplazos_cols, ["numero_serie","numero_serie_idx","n_mero_serie","serial","serie"], "serie_val")}
        LIMIT 200
    """, {"serie_val": serie_val})

    cont_select_candidates = [
        "n_mero_serie","nombre_cuenta","fabricante","modelo","direcci_n_ip",
        "total_p_ginas_mono","total_p_ginas_color","_ltima_fecha_auditor_a_medidores","reportdate","sourcefile",
    ]
    cont_select = ", ".join(f"`{c}`" for c in cont_select_candidates if c in cont_cols) or "*"
    contadores = safe_one(f"""
        SELECT {cont_select}
        FROM printanista.reportes_dispositivos
        WHERE {build_where(cont_cols, ["n_mero_serie","numero_serie","serial","serie"], "serie_val")}
        ORDER BY `id` DESC
        LIMIT 1
    """, {"serie_val": serie_val})

    return {"resumen": resumen, "insumos": insumos, "alertas": alertas, "reemplazos": reemplazos, "contadores": contadores}

# ---------------- dashboard endpoints ----------------

@app.get("/api/reports/overview")
def reports_overview():
    resumen_cols = get_columns("printanista_insumos", "vw_equipo_insumos_con_alertas")
    equipos_con_alertas = None
    if "alertas_total" in resumen_cols:
        equipos_con_alertas = safe_count("""
            SELECT COUNT(*) AS total
            FROM printanista_insumos.vw_equipo_insumos_con_alertas
            WHERE alertas_total > 0
        """)

    return {
        "equipos_con_alertas": equipos_con_alertas,
        "alertas_activas": safe_count("SELECT COUNT(*) AS total FROM printanista_alertas.vw_alertas_actives"),
        "reemplazos": safe_count("SELECT COUNT(*) AS total FROM printanista_reemplazos.vw_reemplazos_insumos_pct"),
        "equipos_resumen": safe_count("SELECT COUNT(*) AS total FROM printanista_insumos.vw_equipo_insumos_resumen"),
    }

@app.get("/api/dashboard/kpis")
def dashboard_kpis():
    equipos_monitoreados = safe_count("SELECT COUNT(DISTINCT numero_serie_idx) AS total FROM printanista_insumos.dispositivos_detallado_gv2")
    alertas_activas = safe_count("SELECT COUNT(*) AS total FROM printanista_alertas.alertas_actives")
    reemplazos = safe_count("SELECT COUNT(*) AS total FROM printanista_reemplazos.reemplazos_insumos_gv")
    paginas = safe_one("""
        SELECT
            COALESCE(SUM(CAST(NULLIF(total_p_ginas_mono,'') AS UNSIGNED)),0) AS mono,
            COALESCE(SUM(CAST(NULLIF(total_p_ginas_color,'') AS UNSIGNED)),0) AS color
        FROM printanista.reportes_dispositivos
    """) or {"mono": 0, "color": 0}
    clientes = safe_count("SELECT COUNT(DISTINCT nombre_cuenta) AS total FROM printanista.reportes_dispositivos")
    return {
        "equipos_monitoreados": equipos_monitoreados,
        "alertas_activas": alertas_activas,
        "reemplazos": reemplazos,
        "paginas_mono": int(paginas.get("mono") or 0),
        "paginas_color": int(paginas.get("color") or 0),
        "clientes": clientes,
        "porc_equipos_con_alertas": round((alertas_activas / equipos_monitoreados) * 100, 2) if equipos_monitoreados else 0,
    }

@app.get("/api/dashboard/alertas-por-cliente")
def dashboard_alertas_por_cliente(limit: int = Query(default=10, ge=1, le=30)):
    cols = get_columns("printanista_alertas", "vw_alertas_actives")
    cliente_col = pick_first(cols, ["nombre_cuenta", "cliente", "cuenta"])
    if not cliente_col:
        return []
    return safe_rows(f"""
        SELECT `{cliente_col}` AS name, COUNT(*) AS total
        FROM printanista_alertas.vw_alertas_actives
        GROUP BY `{cliente_col}`
        ORDER BY total DESC
        LIMIT {int(limit)}
    """)

@app.get("/api/dashboard/alertas-por-fabricante")
def dashboard_alertas_por_fabricante(limit: int = Query(default=10, ge=1, le=30)):
    cols = get_columns("printanista_alertas", "vw_alertas_actives")
    fab_col = pick_first(cols, ["fabricante", "marca"])
    if not fab_col:
        return []
    return safe_rows(f"""
        SELECT `{fab_col}` AS name, COUNT(*) AS total
        FROM printanista_alertas.vw_alertas_actives
        GROUP BY `{fab_col}`
        ORDER BY total DESC
        LIMIT {int(limit)}
    """)

@app.get("/api/dashboard/reemplazos-por-mes")
def dashboard_reemplazos_por_mes(limit: int = Query(default=12, ge=1, le=24)):
    cols = get_columns("printanista_reemplazos", "reemplazos_insumos_gv")
    dt_col = pick_first(cols, ["report_date", "fecha_de_reemplazo", "fecha_instalacion"])
    if not dt_col:
        return []
    return safe_rows(f"""
        SELECT DATE_FORMAT(`{dt_col}`, '%%Y-%%m') AS name, COUNT(*) AS total
        FROM printanista_reemplazos.reemplazos_insumos_gv
        WHERE `{dt_col}` IS NOT NULL AND `{dt_col}` <> ''
        GROUP BY DATE_FORMAT(`{dt_col}`, '%%Y-%%m')
        ORDER BY name DESC
        LIMIT {int(limit)}
    """)

@app.get("/api/dashboard/top-mono")
def dashboard_top_mono(limit: int = Query(default=10, ge=1, le=30)):
    return safe_rows(f"""
        SELECT COALESCE(n_mero_serie,'SIN SERIE') AS name,
               CAST(NULLIF(total_p_ginas_mono,'') AS UNSIGNED) AS total
        FROM printanista.reportes_dispositivos
        WHERE NULLIF(total_p_ginas_mono,'') IS NOT NULL
        ORDER BY total DESC
        LIMIT {int(limit)}
    """)

@app.get("/api/dashboard/top-color")
def dashboard_top_color(limit: int = Query(default=10, ge=1, le=30)):
    return safe_rows(f"""
        SELECT COALESCE(n_mero_serie,'SIN SERIE') AS name,
               CAST(NULLIF(total_p_ginas_color,'') AS UNSIGNED) AS total
        FROM printanista.reportes_dispositivos
        WHERE NULLIF(total_p_ginas_color,'') IS NOT NULL
        ORDER BY total DESC
        LIMIT {int(limit)}
    """)

@app.get("/api/dashboard/equipos-por-fabricante")
def dashboard_equipos_por_fabricante(limit: int = Query(default=10, ge=1, le=30)):
    return safe_rows(f"""
        SELECT COALESCE(fabricante,'SIN FABRICANTE') AS name, COUNT(*) AS total
        FROM printanista.reportes_dispositivos
        GROUP BY fabricante
        ORDER BY total DESC
        LIMIT {int(limit)}
    """)

# ---------------- import/sync endpoints ----------------

@app.post("/api/import/bd1")
async def api_import_bd1(file: UploadFile = File(...)):
    data = await file.read()
    return load_bd1_manual(data, file.filename)

@app.post("/api/import/bd3")
async def api_import_bd3(file: UploadFile = File(...)):
    data = await file.read()
    return load_bd3_manual(data, file.filename)

@app.post("/api/sync/bd2")
def api_sync_bd2(max_results: int = Query(default=100, ge=1, le=500)):
    return sync_bd2_alertas(max_results=max_results)

@app.post("/api/sync/bd3")
def api_sync_bd3(max_results: int = Query(default=100, ge=1, le=500)):
    return sync_bd3_insumos(max_results=max_results)

@app.post("/api/sync/bd4")
def api_sync_bd4(max_results: int = Query(default=100, ge=1, le=500)):
    return sync_bd4_reemplazos(max_results=max_results)

if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")
