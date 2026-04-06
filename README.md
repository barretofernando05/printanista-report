# Printanista Report

## Archivos
- Copia tu dump original a `db/full_dump.sql`
- Los grants iniciales ya están en `db/002_grants.sql`

## Levantar por primera vez
```bash
docker compose down -v
docker compose up --build
```

## Levantar sin perder datos
```bash
docker compose up --build -d
```

## URLs
- App: http://localhost:8000
- Health: http://localhost:8000/api/health
- Tablas: http://localhost:8000/api/debug/tables
- Columnas: http://localhost:8000/api/debug/columns

## Notas
- La app consulta las vistas reales y detecta nombres de columnas en tiempo de ejecución.
- El dump solo se aplica cuando el volumen de MariaDB está vacío.
