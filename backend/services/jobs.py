import json
from typing import Any
from ..db import exec_sql, one

def create_job(job_name: str, source_type: str, source_name: str | None):
    exec_sql("""
        INSERT INTO job_runs (job_name, source_type, source_name, status, started_at)
        VALUES (:job_name, :source_type, :source_name, 'running', NOW())
    """, {"job_name": job_name, "source_type": source_type, "source_name": source_name})
    r = one("SELECT LAST_INSERT_ID() AS id")
    return int((r or {"id": 0})["id"])

def finish_job(job_id: int, status: str, *, files_found=0, files_processed=0, files_skipped=0,
               rows_inserted=0, rows_updated=0, rows_ignored=0, error_text=None, details=None):
    exec_sql("""
        UPDATE job_runs
        SET status=:status, finished_at=NOW(), files_found=:files_found, files_processed=:files_processed,
            files_skipped=:files_skipped, rows_inserted=:rows_inserted, rows_updated=:rows_updated,
            rows_ignored=:rows_ignored, error_text=:error_text, details_json=:details
        WHERE id=:job_id
    """, {
        "status": status, "files_found": files_found, "files_processed": files_processed,
        "files_skipped": files_skipped, "rows_inserted": rows_inserted, "rows_updated": rows_updated,
        "rows_ignored": rows_ignored, "error_text": error_text,
        "details": json.dumps(details or {}, ensure_ascii=False), "job_id": job_id
    })

def add_job_item(job_id: int, file_name: str | None, file_sha1: str | None, target_table: str | None,
                 action_taken: str, rows_inserted=0, rows_updated=0, rows_ignored=0, message=None):
    exec_sql("""
        INSERT INTO job_run_items
        (job_run_id, file_name, file_sha1, target_table, action_taken, rows_inserted, rows_updated, rows_ignored, message)
        VALUES (:job_run_id, :file_name, :file_sha1, :target_table, :action_taken, :rows_inserted, :rows_updated, :rows_ignored, :message)
    """, {
        "job_run_id": job_id, "file_name": file_name, "file_sha1": file_sha1, "target_table": target_table,
        "action_taken": action_taken, "rows_inserted": rows_inserted, "rows_updated": rows_updated,
        "rows_ignored": rows_ignored, "message": message
    })
