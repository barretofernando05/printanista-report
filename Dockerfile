FROM node:20 AS frontend-builder
WORKDIR /frontend
COPY package.json vite.config.js index.html ./
COPY src ./src
RUN npm install
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY --from=frontend-builder /frontend/dist ./dist
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
