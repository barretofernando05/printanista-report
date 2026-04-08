import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .bootstrap import ensure_all
from .db import engine
from .routes.dashboard import router as dashboard_router
from .routes.operaciones import router as operaciones_router
from .routes.consulta import router as consulta_router
from .routes.importacion import router as importacion_router
from .routes.historial import router as historial_router

app = FastAPI(title="Printanista v8", version="8.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    ensure_all()

@app.get("/api/health")
def health():
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True}

app.include_router(dashboard_router)
app.include_router(operaciones_router)
app.include_router(consulta_router)
app.include_router(importacion_router)
app.include_router(historial_router)

if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")
