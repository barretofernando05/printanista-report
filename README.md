# Printanista Proyecto Corregido

## Qué resuelve
- La raíz `/` abre la aplicación para usuarios.
- Las rutas `/api/...` quedan separadas para backend.
- Tiene dashboard, línea de tiempo, detalle por cliente, búsqueda por serie y panel de importación.
- Registra jobs en `job_runs` y `job_run_items`.

## Estructura esperada
- `db/full_dump.sql` → tu dump inicial
- `db/002_grants.sql`
- `db/003_jobs.sql`
- `secrets/token_technoma.json` → reservado para futuras integraciones

## Levantar por primera vez
```bash
docker compose down -v
docker compose up --build
```

## Actualizar sin perder la base
```bash
docker compose down
docker compose up --build -d
```

## URL para usuarios
```text
http://TU_IP:8000
```

## APIs
- `/api/health`
- `/api/dashboard/summary`
- `/api/detail/alertas`
- `/api/equipo/{serie}`
- `/api/jobs`
- `/api/import/bd1`
- `/api/import/bd3`
