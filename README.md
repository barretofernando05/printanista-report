# Printanista Report V5.1

Incluye:
- dashboard con KPIs y gráficos
- consulta por serie
- importación manual BD1 y BD3
- sync Gmail BD2/BD3/BD4
- sync global
- historial de jobs
- scheduler automático

Token Gmail:
./secrets/token_technoma.json

Primera carga:
docker compose down -v
docker compose up --build

Actualizar solo código:
docker compose down
git pull
docker compose up --build -d


Cambios de V5.1:
- fix de get_columns() para SQLAlchemy mappings
- frontend tolerante a errores no JSON
