# Printanista v8 Modular

## Qué trae
- Inicio
- Reemplazos (BD3)
- Equipos sin reportar (BD1)
- Series repetidas (BD1)
- Consulta por serie (BD1/BD2/BD3/BD4)
- Importación / Sync
- Historial
- Backend y frontend separados y modulares

## Cómo reajustar tu proyecto actual
1. Haz backup del proyecto actual.
2. Reemplaza tu estructura por esta:
   - `backend/`
   - `frontend/`
   - `db/`
   - `Dockerfile`
   - `docker-compose.yml`
   - `requirements.txt`
3. Copia tu dump real a:
   - `db/full_dump.sql`
4. Copia tu token a:
   - `secrets/token_technoma.json`
5. Levanta con:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

## Qué ajustaremos luego al final en base de datos
- Confirmar columnas reales de `reemplazos_insumos_gv`
- Confirmar si existen `rpt_serie_status` y `rpt_serie_cliente`
- Afinar joins del resumen por serie
- Reglas reales de reemplazos innecesarios / no nuevos
- Exportación CSV/XLSX real
- Paginación avanzada
- Mejoras de performance (cache / índices)

## Nota
La estructura funcional completa ya queda armada. Lo siguiente es alinear fino las consultas con tu base real.
