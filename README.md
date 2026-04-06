# Printanista Report V3

## Qué incluye
- Consulta por serie en una sola web
- Importación manual BD1
- Importación manual BD3
- Sync Gmail BD2 / BD3 / BD4

## Gmail
Monta tu token aquí:
`./secrets/token_technoma.json`

Ya está montado en docker-compose como:
`./secrets:/app/secrets:ro`

## Primera carga con dump
```bash
docker compose down -v
docker compose up --build
```

## Actualizar solo código
```bash
docker compose down
git pull
docker compose up --build -d
```

## URLs
- App: http://localhost:8000
- Health: http://localhost:8000/api/health
- Tablas: http://localhost:8000/api/debug/tables
- Columnas: http://localhost:8000/api/debug/columns

## Importación
- Manual BD1: desde la UI
- Manual BD3: desde la UI
- Sync Gmail BD2/BD3/BD4: desde la UI
