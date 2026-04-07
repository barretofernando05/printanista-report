FROM node:20 as fe
WORKDIR /f
COPY frontend .
RUN npm install && npm run build

FROM python:3.11
WORKDIR /app
COPY backend/app.py .
RUN pip install fastapi uvicorn pymysql sqlalchemy
COPY --from=fe /f/dist ./dist
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
