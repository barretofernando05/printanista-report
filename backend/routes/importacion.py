from fastapi import APIRouter, File, UploadFile
from ..services.imports import generic_manual_import, sync_bd1_from_gmail, sync_gmail_generic

router = APIRouter(prefix="/api", tags=["importacion"])

@router.post("/import/bd1")
async def import_bd1(file: UploadFile = File(...)):
    return await generic_manual_import(file, "bd1_manual", "reportes_dispositivos")

@router.post("/import/bd3")
async def import_bd3(file: UploadFile = File(...)):
    return await generic_manual_import(file, "bd3_manual", "printanista_insumos.dispositivos_detallado_gv2")

@router.post("/sync/bd1")
def sync_bd1():
    return sync_bd1_from_gmail()

@router.post("/sync/bd2")
def sync_bd2():
    return sync_gmail_generic("bd2_sync", "Gmail BD2 Alertas", 'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts") newer_than:60d', "printanista_alertas.alertas_actives")

@router.post("/sync/bd3")
def sync_bd3():
    return sync_gmail_generic("bd3_sync", "Gmail BD3 Dispositivos", 'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d', "printanista_insumos.dispositivos_detallado_gv2")

@router.post("/sync/bd4")
def sync_bd4():
    return sync_gmail_generic("bd4_sync", "Gmail BD4 Reemplazos", 'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d', "printanista_reemplazos.reemplazos_insumos_gv")

@router.post("/sync/all")
def sync_all():
    r1 = sync_bd1_from_gmail()
    r2 = sync_gmail_generic("bd2_sync_all", "Gmail BD2 Alertas", 'from:no-reply@printanistahub.com (subject:"Alertas" OR subject:"Active Alerts") newer_than:60d', "printanista_alertas.alertas_actives")
    r3 = sync_gmail_generic("bd3_sync_all", "Gmail BD3 Dispositivos", 'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d', "printanista_insumos.dispositivos_detallado_gv2")
    r4 = sync_gmail_generic("bd4_sync_all", "Gmail BD4 Reemplazos", 'from:no-reply@printanistahub.com subject:"Reporte Programado v4" filename:xlsx newer_than:60d', "printanista_reemplazos.reemplazos_insumos_gv")
    return {"status":"ok","children":{"bd1":r1,"bd2":r2,"bd3":r3,"bd4":r4}}
