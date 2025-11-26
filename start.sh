#!/bin/sh
# Start script for Railway deployment
# Handles PORT environment variable properly

PORT=${PORT:-8000}
echo "Starting uvicorn on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
