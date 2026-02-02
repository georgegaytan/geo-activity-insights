# Geo Activity Insights

Prototype system for ingesting geospatial workout activities, storing them in PostGIS, and generating asynchronous AI-powered insight reports.

## Overview

- Ingests workout activities from a simulated Strava-like webhook
- Stores geospatial routes in PostgreSQL with PostGIS
- Exposes REST APIs for listing activities, searching nearby routes, and generating insights
- Uses a Redis-backed queue and worker to generate insight reports
- React + TypeScript + TanStack Query frontend

## Project Structure

- `backend/` – FastAPI app, SQLAlchemy models, services, REST API
- `worker/` – Python worker consuming jobs from Redis and updating insight reports
- `frontend/` – Vite + React + TS + TanStack Query SPA
- `docker-compose.yml` – Dev stack with PostGIS, Redis, backend, worker, frontend

## Backend

### Tech

- FastAPI
- SQLAlchemy
- PostgreSQL + PostGIS (via `postgis/postgis` Docker image)
- GeoAlchemy2 + Shapely for geospatial LINESTRING routes
- Redis for background job queue

### Models

- **User**
  - `id` (UUID, pk)
  - `email`
  - `created_at`
- **Activity**
  - `id` (UUID, pk)
  - `user_id` (fk)
  - `external_id` (unique)
  - `source` (string)
  - `start_time` (datetime)
  - `duration_seconds` (int)
  - `distance_meters` (int)
  - `avg_heart_rate` (int, nullable)
  - `route` (PostGIS geography LINESTRING)
- **InsightReport**
  - `id` (UUID, pk)
  - `activity_id` (fk)
  - `status` (pending, processing, done, failed)
  - `summary` (text, nullable)
  - `created_at`

### Key API Endpoints

- `POST /webhooks/strava`
  - Accepts an activity payload
  - Upserts `Activity` using `external_id`
  - Stores route as geography `LINESTRING`

- `GET /activities`
  - Returns list of activities

- `GET /activities/nearby?lat=&lon=&radius_meters=`
  - Uses PostGIS `ST_DWithin` to find activities whose route is within radius of given point

- `POST /activities/{id}/generate-insight`
  - Creates `InsightReport` with status `pending`
  - Pushes job to Redis queue

- `GET /insights/{id}`
  - Returns insight status and summary

## Worker

- Polls a Redis list-based queue for jobs
- Each job references an `InsightReport` ID
- Loads the activity and recent activities for the same user in the past 7 days
- Builds a short, structured natural-language summary
- Uses a mock LLM call function (easily swappable later)
- Saves the summary and marks the report as `done`

Run locally (without Docker):

```bash
# from backend/
pip install -r requirements.txt
uvicorn app.main:app --reload

# in another shell, from project root
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/geo_activities
export REDIS_URL=redis://localhost:6379/0
python -m worker.worker
```

You must have PostgreSQL+PostGIS and Redis running.

## Frontend

- Vite + React + TypeScript
- TanStack Query for data fetching, caching, and polling

### Pages / Features

- **Activity Dashboard**
  - Fetches `/activities`
  - Renders table of workouts with distance, duration, HR
  - "Generate Insight" button per activity calls `POST /activities/{id}/generate-insight`
- **Nearby Search**
  - Lat/lon/radius form
  - Calls `/activities/nearby`
  - Displays count of results
- **Insight Generator**
  - After creating an insight, polls `/insights/{id}` every 3 seconds
  - Shows status and AI-generated summary

Run locally (without Docker):

```bash
cd frontend
npm install
npm run dev
```

By default, the frontend talks to `http://localhost:8000`. You can override via `VITE_API_BASE`.

## Running with Docker Compose

From the project root:

```bash
docker compose up --build
```

Services:

- `db` – Postgres + PostGIS on `localhost:5432`
- `redis` – Redis on `localhost:6379`
- `backend` – FastAPI on `http://localhost:8000`
- `worker` – Background worker process
- `frontend` – React app on `http://localhost:5173`

## Example Strava Webhook Payload

Example `curl` request to simulate an incoming Strava-like webhook:

```bash
curl -X POST http://localhost:8000/webhooks/strava \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "external_id": "strava-activity-123",
    "source": "strava",
    "start_time": "2024-01-01T07:30:00Z",
    "duration_seconds": 3600,
    "distance_meters": 10000,
    "avg_heart_rate": 150,
    "route": [
      {"lat": 47.3769, "lon": 8.5417},
      {"lat": 47.3742, "lon": 8.5442}
    ]
  }'
```

## AWS Deployment Sketch

### Overview

A realistic AWS deployment could look like:

- **API Gateway + Lambda** for the FastAPI app (via an adapter such as Mangum / AWS Lambda Powertools)
- **RDS Postgres** with PostGIS enabled for geospatial storage
- **SQS** as the background job queue
- **Lambda or Fargate worker** for processing insight jobs
- **CloudFront + S3** for serving the frontend SPA

### Components

- **FastAPI as Lambda**
  - Package FastAPI app plus dependencies into a Lambda function
  - Use API Gateway (HTTP API) to expose `/webhooks/strava`, `/activities`, `/activities/nearby`, `/activities/{id}/generate-insight`, `/insights/{id}`
  - Configure environment variables (`DATABASE_URL`, etc.) via Lambda configuration or Secrets Manager

- **RDS Postgres with PostGIS**
  - Use an Amazon RDS PostgreSQL instance/cluster
  - Enable PostGIS extension (`CREATE EXTENSION postgis;`)
  - VPC configuration required to allow Lambda and worker access

- **SQS Queue**
  - Replace the Redis list queue with SQS
  - On `POST /activities/{id}/generate-insight`, publish a message to SQS containing the `InsightReport` ID

- **Worker (Lambda or Fargate)**
  - **Lambda option**: configure an SQS-triggered Lambda that receives messages, loads the activity/insight from RDS, calls the LLM API, and updates `InsightReport`
  - **Fargate option**: run a containerized worker that polls SQS

- **Frontend**
  - Build the Vite app (`npm run build`)
  - Upload the `dist/` contents to an S3 bucket configured for static website hosting
  - Put CloudFront in front of S3 for CDN, HTTPS, and custom domain

### Observability & Ops

- Use CloudWatch Logs for Lambda and Fargate logs
- Add metrics on request latency, error counts, worker throughput
- Use AWS Systems Manager Parameter Store or Secrets Manager for DB credentials and API keys (for the real LLM provider)

---

This repo is a prototype and not hardened for production (no migrations, limited validation, minimal auth). For a production system, add:

- Alembic migrations
- Auth (e.g., Cognito, OAuth)
- More robust error handling and logging
- Rate limiting and webhook signature verification
- Real LLM integration with secure API key management
