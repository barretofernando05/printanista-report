# Printanista Report V4

## Incluye
- Dashboard estético con KPIs y gráficos
- Consulta por serie
- Importación manual BD1
- Importación manual BD3
- Sync Gmail BD2 / BD3 / BD4
- Reportes globales robustos

## Token Gmail
Coloca tu token en:
`./secrets/token_technoma.json`

## Primera carga con dump
```bash
docker compose down -v
docker compose up --build
```

## Actualizar solo código sin perder la base
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
- KPIs: http://localhost:8000/api/dashboard/kpis
