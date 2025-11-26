# Dhruva Backend Dockerfile for Railway
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ML and PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create __init__.py in ml directory if missing
RUN touch /app/ml/__init__.py

# Make start script executable
RUN chmod +x /app/start.sh

# Ensure ML models directory is accessible
ENV PYTHONPATH=/app:/app/ml

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Railway sets PORT env var dynamically
EXPOSE 8000

# Use entrypoint script for proper variable expansion
ENTRYPOINT ["/app/start.sh"]
