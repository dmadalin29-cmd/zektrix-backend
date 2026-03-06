# Dockerfile for Backend

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Copy application
COPY . .

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
