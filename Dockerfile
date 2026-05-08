FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/ backend/
COPY frontend/ frontend/

# Cloud Run injects the PORT environment variable. We default to 8080 for local testing.
ENV PORT=8080

# Run Uvicorn using the PORT environment variable
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
