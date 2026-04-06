# Printanista Report

## Arranque

1. Copia tu dump real a `db/full_dump.sql`
2. Ejecuta:

```bash
docker compose down -v
docker compose up --build
```

## Acceso

- App: http://localhost:8000
- Health: http://localhost:8000/api/health
- Tablas detectadas: http://localhost:8000/api/debug/tables

## Notas
- La app consulta vistas reales:
  - `printanista_insumos.vw_equipo_insumos_con_alertas`
  - `printanista_insumos.vw_equipo_insumos_resumen`
  - `printanista_insumos.vw_equipo_insumos_detalle`
  - `printanista_alertas.vw_alertas_actives`
  - `printanista_reemplazos.vw_reemplazos_insumos_pct`
- Los contadores salen desde `printanista.reportes_dispositivos`
