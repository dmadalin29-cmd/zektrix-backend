FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY backend/requirements.txt ./backend/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend/requirements.txt && \
    pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && \
    pip install pywebpush py-vapid

COPY . .

ENV PYTHONUNBUFFERED=1

CMD pip install pywebpush py-vapid --quiet 2>/dev/null; uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8080}
