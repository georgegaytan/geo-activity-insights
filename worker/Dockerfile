# Use a slim Python image
FROM python:3.14-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies needed for building Python packages like Shapely
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libblas-dev \
    liblapack-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (shared models, db, etc.)
COPY backend/app ./app

# Copy worker code
COPY worker/worker.py ./worker/worker.py

# Default command to run the worker
CMD ["python", "-m", "worker.worker"]
