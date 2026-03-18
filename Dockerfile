FROM python:3.11-slim

# Force rebuild - changed $(date)
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install ALL Python deps
COPY requirements.txt .
COPY backend/requirements.txt ./backend_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend_requirements.txt && \
    pip install --no-cache-dir pywebpush py-vapid && \
    pip install --no-cache-dir emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && \
    python -c "from pywebpush import webpush; print('pywebpush OK')"

COPY . .

ENV PYTHONUNBUFFERED=1

# Ensure pywebpush at runtime too
CMD python -c "import pywebpush; print('pywebpush available')" && uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8080}
