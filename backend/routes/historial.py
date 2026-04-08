from fastapi import APIRouter
from ..db import safe_rows, safe_one

router = APIRouter(prefix="/api/jobs", tags=["historial"])

@router.get("")
def jobs():
    return safe_rows("SELECT * FROM job_runs ORDER BY id DESC LIMIT 200")

@router.get("/{job_id}")
def job_detail(job_id: int):
    return {
        "job": safe_one("SELECT * FROM job_runs WHERE id = :id", {"id": job_id}),
        "items": safe_rows("SELECT * FROM job_run_items WHERE job_run_id = :id ORDER BY id DESC", {"id": job_id}),
    }
