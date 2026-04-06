import io
import os
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base


DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "printanista")
DB_USER = os.getenv("DB_USER", "printanista")
DB_PASSWORD = os.getenv("DB_PASSWORD", "printanista123")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI(title="Printanista Report")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PrinterRecord(Base):
    __tablename__ = "printer_records"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String(100), index=True, nullable=False)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(150), nullable=True)
    client = Column(String(150), nullable=True)
    ip_address = Column(String(50), nullable=True)
    last_report = Column(String(50), nullable=True)
    total_mono = Column(String(50), nullable=True)
    total_color = Column(String(50), nullable=True)
    raw_data = Column(Text, nullable=True)


Base.metadata.create_all(bind=engine)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def find_value(row: dict, possible_columns: List[str]) -> Optional[str]:
    for col in possible_columns:
        if col in row and pd.notna(row[col]):
            return str(row[col])
    return None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/records")
def list_records(limit: int = Query(default=100, le=500)):
    db = SessionLocal()
    try:
        rows = db.query(PrinterRecord).limit(limit).all()
        return [
            {
                "id": r.id,
                "serial": r.serial,
                "manufacturer": r.manufacturer,
                "model": r.model,
                "client": r.client,
                "ip_address": r.ip_address,
                "last_report": r.last_report,
                "total_mono": r.total_mono,
                "total_color": r.total_color,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/api/records/{serial}")
def get_record_by_serial(serial: str):
    db = SessionLocal()
    try:
        row = db.query(PrinterRecord).filter(PrinterRecord.serial == serial).first()
        if not row:
            raise HTTPException(status_code=404, detail="No se encontró el equipo.")
        return {
            "id": row.id,
            "serial": row.serial,
            "manufacturer": row.manufacturer,
            "model": row.model,
            "client": row.client,
            "ip_address": row.ip_address,
            "last_report": row.last_report,
            "total_mono": row.total_mono,
            "total_color": row.total_color,
            "raw_data": row.raw_data,
        }
    finally:
        db.close()


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    db = SessionLocal()
    processed = 0

    try:
        for file in files:
            content = await file.read()

            try:
                if file.filename.lower().endswith(".csv"):
                    df = pd.read_csv(io.BytesIO(content))
                elif file.filename.lower().endswith((".xlsx", ".xls")):
                    df = pd.read_excel(io.BytesIO(content))
                else:
                    raise HTTPException(status_code=400, detail=f"Formato no soportado: {file.filename}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error leyendo {file.filename}: {e}")

            df = normalize_columns(df)

            for _, row in df.iterrows():
                row_dict = row.to_dict()

                serial = find_value(row_dict, ["serial", "numero_serie", "nro_serie", "serie"])
                if not serial:
                    continue

                manufacturer = find_value(row_dict, ["manufacturer", "fabricante", "marca"])
                model = find_value(row_dict, ["model", "modelo"])
                client = find_value(row_dict, ["client", "cliente", "cuenta"])
                ip_address = find_value(row_dict, ["ip_address", "ip", "direccion_ip"])
                last_report = find_value(row_dict, ["last_report", "ultimo_reporte", "fecha_reporte"])
                total_mono = find_value(row_dict, ["total_mono", "mono_total", "contador_mono"])
                total_color = find_value(row_dict, ["total_color", "color_total", "contador_color"])

                existing = db.query(PrinterRecord).filter(PrinterRecord.serial == serial).first()

                if existing:
                    existing.manufacturer = manufacturer
                    existing.model = model
                    existing.client = client
                    existing.ip_address = ip_address
                    existing.last_report = last_report
                    existing.total_mono = total_mono
                    existing.total_color = total_color
                    existing.raw_data = str(row_dict)
                else:
                    db.add(
                        PrinterRecord(
                            serial=serial,
                            manufacturer=manufacturer,
                            model=model,
                            client=client,
                            ip_address=ip_address,
                            last_report=last_report,
                            total_mono=total_mono,
                            total_color=total_color,
                            raw_data=str(row_dict),
                        )
                    )

                processed += 1

        db.commit()
        return {"message": "Archivos procesados correctamente", "rows_processed": processed}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")