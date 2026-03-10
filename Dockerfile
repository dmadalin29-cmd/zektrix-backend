FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Copy backend code
COPY backend/ .

# Expose port (Railway uses dynamic PORT)
EXPOSE 8001

# Run the application - use PORT env variable from Railway
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}
