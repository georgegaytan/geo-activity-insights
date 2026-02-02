# Geo Activity Insights

**A production‑grade, end‑to‑end geospatial activity platform built in a single day.**  
Ingests Strava workouts, stores routes in PostGIS, and serves AI‑powered insights via a modern React frontend. Demonstrates full‑stack design, clean architecture, and scalable deployment patterns.

> **TL;DR**  
> - FastAPI + SQLAlchemy + PostGIS for geo data  
> - Redis‑backed async worker for insight generation  
> - React + TypeScript + TanStack Query frontend  
> - Docker Compose dev stack; AWS‑ready deployment sketch  
> - Strava OAuth integration with token persistence and activity import

## Proof of Concept Example

<img width="940" height="1055" alt="image" src="https://github.com/user-attachments/assets/bef63c06-5da7-4a88-94f9-88762750a66f" />

---

## Architecture Overview

```
┌─────────────┐   OAuth   ┌─────────────┐   Webhook ┌─────────────┐
│   Strava    │◄─────────►│   FastAPI   │◄─────────►│   Strava    │
│   API       │           │   Backend   │           │   Webhook   │
└─────────────┘           └─────┬───────┘           └─────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
┌──────▼───────┐    ┌────────────▼─────┐    ┌──────────────▼──────┐
│ PostgreSQL   │    │   Redis Queue    │    │   Worker (Python)   │
│ + PostGIS    │    │   (RQ‑style)     │    │   + Mock LLM        │
└──────────────┘    └──────────────────┘    └─────────────────────┘
                                 │
                         ┌───────▼───────┐
                         │   React SPA   │
                         │  + TanStack   │
                         └───────────────┘
```

## Core Features

- **Strava OAuth 2.0** – Authorization, token exchange, persistence, and automatic refresh.
- **Activity Ingestion** – Webhook‑compatible upserts with PostGIS `LINESTRING` route storage.
- **Geospatial Queries** – Fast `ST_DWithin` radius search on activity routes.
- **Async Insight Generation** – Redis‑backed job queue; worker aggregates recent activity context and produces AI‑style summaries.
- **Realtime UI** – TanStack Query polling, loading/error states, and optimistic cache updates.
- **Migration‑Managed Schema** – Alembic with PostGIS extension creation.
- **Secret‑Safe Config** – `.env` files and Docker Compose env expansion; no leaked credentials.

---

## Data Model

| Entity | Key Fields | Notes |
|--------|------------|-------|
| `User` | `id` (UUID), `email` | Synthetic user per Strava athlete. |
| `Activity` | `id`, `user_id`, `external_id`, `source`, `start_time`, `duration_seconds`, `distance_meters`, `avg_heart_rate`, `route` (PostGIS) | Upserted by webhook or import. |
| `InsightReport` | `id`, `activity_id`, `status` (`pending|processing|done|failed`), `summary`, `created_at` | Generated asynchronously. |
| `StravaAccount` | `id`, `user_id`, `athlete_id`, `access_token`, `refresh_token`, `expires_at` | Stores OAuth tokens per athlete. |

## API Highlights

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/strava` | Ingest/upsert an activity (webhook‑compatible). |
| `GET` | `/activities` | List all activities (paginated in a real system). |
| `GET` | `/activities/nearby?lat=&lon=&radius_meters=` | Geospatial radius search via PostGIS. |
| `POST` | `/activities/{id}/generate-insight` | Queue an insight job for an activity. |
| `GET` | `/insights/{id}` | Poll insight status and summary. |
| `GET` | `/strava/oauth/callback` | OAuth redirect handler (HTML page with code). |
| `POST` | `/strava/oauth/exchange` | Exchange code → tokens; persist `StravaAccount`. |
| `POST` | `/strava/import-activities` | Pull recent activities via Strava API and upsert them. |

---

## Development Workflow

```bash
# Clone and configure
git clone <repo>
cd geo-activity-insights
cp .env.example .env          # Add your STRAVA_CLIENT_SECRET
cp backend/.env.example backend/.env

# Full stack (Docker Compose)
docker compose up --build

# Run Alembic migrations once
docker compose exec backend alembic upgrade head
```

### Local (non‑Docker) development

```bash
# Backend
cd backend
uv pip install -r requirements.txt
uvicorn app.main:app --reload

# Worker (in another shell)
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/geo_activities
export REDIS_URL=redis://localhost:6379/0
python -m worker.worker

# Frontend
cd frontend
npm install
npm run dev
```

---

## Frontend Architecture

- **TanStack Query** – Cache, dedupe, and poll backend data.
- **React + TypeScript** – Type‑safe component layer.
- **Vite** – Fast dev server and optimized builds.
- **Strava UI Flow** – Authorize → paste code → exchange → import → dashboard.

Key queries:
- `useQuery(['activities'], fetchActivities)`
- `useQuery(['nearby', params], fetchNearby)`
- `useMutation(importStravaActivities)` with `onSuccess` cache invalidation.

---

## Production Deployment Sketch (AWS)

| Component | AWS Service | Notes |
|-----------|-------------|-------|
| API | API Gateway + Lambda (FastAPI via Mangum) | HTTP API; env vars via Secrets Manager. |
| DB | RDS PostgreSQL + PostGIS | Multi‑AZ; VPC. |
| Queue | SQS | Replace Redis list; triggers Lambda worker. |
| Worker | Lambda (SQS trigger) or Fargate | Processes insights; calls real LLM. |
| Frontend | CloudFront + S3 (SPA) | CDN + HTTPS. |
| Secrets | Secrets Manager / Parameter Store | DB, Strava, LLM keys. |
| Observability | CloudWatch Logs + X‑Ray | Metrics, tracing. |

---

## Operational Considerations

- **Migrations** – Alembic; run `upgrade head` on deploy.
- **Auth** – Strava OAuth; store `refresh_token` for renewal.
- **Rate limiting** – Apply at API Gateway / web framework level.
- **Webhook verification** – Strava signatures (optional for prod).
- **LLM integration** – Swap mock for OpenAI/Bedrock; guard API keys.
- **Scaling** – Stateless FastAPI; worker scales via SQS concurrency.

---

## Quick Demo

```bash
# 1. Start stack
docker compose up --build && docker compose exec backend alembic upgrade head

# 2. Authorize & import via UI (http://localhost:5173)
#    - Click “Authorize with Strava”
#    - Paste code → Exchange → Import

# 3. Generate an insight
#    - Click “Generate Insight” on any activity row
#    - Watch the Insight Viewer poll until “done”
```

---

## Extending the Platform

- **Additional providers** – Garmin, Polar via webhook adapters.
- **Rich analytics** – Aggregate stats, heatmaps, route clustering.
- **Real-time map** – Leaflet/Mapbox with activity routes.
- **User accounts** – Multi‑user auth; per‑user Strava links.
- **Mobile** – React Native or PWA wrapper.

---

## License

MIT.
