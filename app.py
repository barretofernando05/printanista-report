from fastapi import FastAPI
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://printanista:printanista123@db:3306/printanista")

app = FastAPI()

def q(sql):
    with engine.begin() as c:
        return [dict(r) for r in c.execute(text(sql)).mappings()]

@app.get("/api/dashboard/kpis")
def kpis():
    equipos = q("SELECT COUNT(*) total FROM reportes_dispositivos")[0]["total"]
    alertas = q("SELECT COUNT(*) total FROM printanista_alertas.alertas_actives")[0]["total"]
    return {"equipos": equipos, "alertas": alertas}

@app.get("/api/dashboard/timeline")
def timeline():
    return q(
        "SELECT DATE(report_date) fecha, COUNT(*) total FROM printanista_alertas.alertas_actives GROUP BY DATE(report_date) ORDER BY fecha DESC LIMIT 30"
    )

@app.get("/api/detail")
def detail():
    return q("SELECT * FROM printanista_alertas.alertas_actives LIMIT 100")
