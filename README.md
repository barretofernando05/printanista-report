# Printanista Report corregido

Este proyecto respeta esta estructura:

- `backend/app.py`
- `frontend/`
- `db/`
- `Dockerfile`
- `docker-compose.yml`

## Qué corrige
- La raíz `/` sirve el frontend para usuarios.
- Las rutas `/api/...` quedan para backend.
- Tiene dashboard, línea de tiempo, detalle por cliente, búsqueda por serie y panel de importación.
- Registra jobs en `job_runs` y `job_run_items`.

## Secret
Colocar aquí:
`secrets/token_technoma.json`

## Primera ejecución
```bash
docker compose down -v
docker compose up --build
```

## Actualización normal
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Verificación
- `http://TU_IP:8000` → frontend
- `http://TU_IP:8000/api/health` → health
