from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
import os

app = FastAPI()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER','printanista')}:{os.getenv('DB_PASSWORD','printanista123')}@{os.getenv('DB_HOST','db')}:3306/printanista"
)

def q(sql, p={}):
    with engine.begin() as c:
        return [dict(r) for r in c.execute(text(sql), p).mappings().all()]

def one(sql, p={}):
    with engine.begin() as c:
        r = c.execute(text(sql), p).mappings().first()
        return dict(r) if r else {}

def filters(date_from, date_to):
    f = ["1=1"]
    p={}
    if date_from:
        f.append("report_date>=:d1")
        p["d1"]=date_from
    if date_to:
        f.append("report_date<=:d2")
        p["d2"]=date_to
    return " AND ".join(f), p

@app.get("/api/health")
def health():
    return {"ok":True}

@app.get("/api/dashboard")
def dashboard(date_from: str=None, date_to: str=None):
    w,p = filters(date_from,date_to)

    return {
        "kpis":{
            "equipos": one(f"SELECT COUNT(DISTINCT numero_serie_idx) total FROM printanista_insumos.dispositivos_detallado_gv2 WHERE {w}",p).get("total",0),
            "alertas": one(f"SELECT COUNT(*) total FROM printanista_alertas.alertas_actives WHERE {w}",p).get("total",0),
            "reemplazos": one(f"SELECT COUNT(*) total FROM printanista_reemplazos.reemplazos_insumos_gv WHERE {w}",p).get("total",0),
        },
        "timeline": q(f"SELECT report_date name, COUNT(*) total FROM printanista_alertas.alertas_actives WHERE {w} GROUP BY report_date ORDER BY report_date",p),
        "clientes": q(f"SELECT nombre_cuenta name, COUNT(*) total FROM printanista_alertas.alertas_actives WHERE {w} GROUP BY nombre_cuenta ORDER BY total DESC LIMIT 10",p)
    }

@app.get("/api/detail")
def detail(cliente:str=None):
    sql="SELECT * FROM printanista_alertas.alertas_actives WHERE 1=1"
    p={}
    if cliente:
        sql+=" AND nombre_cuenta=:c"
        p["c"]=cliente
    return q(sql+" LIMIT 200",p)
