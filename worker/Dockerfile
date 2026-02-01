FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY ../backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ../backend/app ./app
COPY worker.py ./worker/worker.py

CMD ["python", "-m", "worker.worker"]
