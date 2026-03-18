FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY backend/requirements.txt ./backend_requirements.txt

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend_requirements.txt && \
    pip install --no-cache-dir pywebpush py-vapid && \
    pip install --no-cache-dir emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && \
    python -c "from pywebpush import webpush; print('pywebpush OK')" && \
    python -c "import emergentintegrations; print('emergentintegrations OK')"

COPY . .

ENV PYTHONUNBUFFERED=1

CMD uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8080}
