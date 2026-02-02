# Use a slim Python image
FROM python:3.14-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies needed for Shapely and numerical packages
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
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app code and Alembic config
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# Expose FastAPI port
EXPOSE 8000

# Command to run the backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
