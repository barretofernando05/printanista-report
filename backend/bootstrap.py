from .db import exec_sql

def ensure_job_tables():
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

def ensure_processed_gmail_messages_table():
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

def ensure_alertas_dashboard_view():
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

def ensure_all():
    for fn in [ensure_job_tables, ensure_processed_gmail_messages_table, ensure_alertas_dashboard_view]:
        try:
            fn()
        except Exception:
            pass
