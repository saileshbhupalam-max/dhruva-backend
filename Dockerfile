# Dhruva Backend Dockerfile for Railway
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ML and PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Ensure ML models directory is accessible
ENV PYTHONPATH=/app:/app/ml

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Railway uses dynamic PORT
EXPOSE 8000

# Run with uvicorn - Railway sets PORT env var
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
