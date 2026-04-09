FROM node:20 AS fe
WORKDIR /f

COPY frontend/package.json frontend/package-lock.json* frontend/vite.config.js frontend/index.html ./
COPY frontend/src ./src

RUN npm install
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY --from=fe /f/dist ./dist

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]