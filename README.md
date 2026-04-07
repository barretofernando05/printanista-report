# Printanista Report 7.1

Estructura respetada:
- `backend/app.py`
- `frontend/`
- `db/`
- `Dockerfile`
- `docker-compose.yml`

## Incluye
- raíz `/` sirviendo el frontend
- filtros por fecha en dashboard y detalle
- importación manual BD1 / BD3
- Gmail Sync BD2 / BD3 / BD4 / All
- historial de jobs
- consulta por serie

## Secret
Colocar en:
`secrets/token_technoma.json`

Se monta dentro del contenedor como:
`/app/secrets/token_technoma.json`

## Primera ejecución
```bash
docker compose down -v
docker compose up --build
```

## Rebuild limpio
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Validación
- `http://TU_IP:8000/`
- `http://TU_IP:8000/api/health`
