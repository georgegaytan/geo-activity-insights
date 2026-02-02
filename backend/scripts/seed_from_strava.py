"""Seed local geo-activity-insights DB with real Strava activities.

This script:
- Uses your Strava access token to call the Strava API.
- Transforms a few recent activities into the webhook payload shape.
- POSTs them to the local backend `/webhooks/strava` endpoint.

Run from the repo root with your virtualenv active:

    cd backend
    export STRAVA_ACCESS_TOKEN=...  # or set in PowerShell
    python scripts/seed_from_strava.py

Environment variables:
- STRAVA_ACCESS_TOKEN (required): a valid Strava access token.
- API_BASE (optional): backend base URL (default http://localhost:8000).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


STRAVA_API_BASE = "https://www.strava.com/api/v3"


def build_webhook_payload(activity: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Map a Strava activity JSON object into our ActivityCreate payload.

    We keep this intentionally simple for seeding:
    - external_id: "strava-<activity_id>"
    - source: "strava"
    - start_time: activity["start_date"]
    - duration_seconds: activity["elapsed_time"]
    - distance_meters: activity["distance"]
    - avg_heart_rate: activity.get("average_heartrate")
    - route: built from start/end latlng if present
    """

    external_id = f"strava-{activity['id']}"

    start = activity.get("start_latlng")
    end = activity.get("end_latlng") or start
    if not start:
        # Skip activities without any location
        raise ValueError("activity has no start_latlng; skipping")

    route = [
        {"lat": start[0], "lon": start[1]},
    ]
    if end and end != start:
        route.append({"lat": end[0], "lon": end[1]})

    payload: Dict[str, Any] = {
        "user_id": user_id,
        "external_id": external_id,
        "source": "strava",
        "start_time": activity["start_date"],
        "duration_seconds": int(activity["elapsed_time"]),
        "distance_meters": int(activity["distance"]),
        "avg_heart_rate": activity.get("average_heartrate"),
        "route": route,
    }
    return payload


def main() -> None:
    api_base = os.getenv("API_BASE", "http://localhost:8000")
    access_token = os.getenv("STRAVA_ACCESS_TOKEN")
    user_id = os.getenv("SEED_USER_ID", "00000000-0000-0000-0000-000000000001")

    if not access_token:
        raise SystemExit("STRAVA_ACCESS_TOKEN environment variable is required")

    print(f"Using API_BASE={api_base}")

    headers = {"Authorization": f"Bearer {access_token}"}

    with httpx.Client(base_url=STRAVA_API_BASE, headers=headers, timeout=20.0) as client:
        resp = client.get("/athlete/activities", params={"per_page": 10, "page": 1})
        resp.raise_for_status()
        activities: List[Dict[str, Any]] = resp.json()

    print(f"Fetched {len(activities)} activities from Strava")

    imported = 0
    errors = 0

    with httpx.Client(base_url=api_base, timeout=20.0) as backend:
        for act in activities:
            try:
                payload = build_webhook_payload(act, user_id=user_id)
            except ValueError as exc:
                print(f"Skipping activity {act.get('id')}: {exc}")
                errors += 1
                continue

            r = backend.post("/webhooks/strava", json=payload)
            if r.status_code >= 400:
                print(f"Failed to import activity {act.get('id')}: {r.status_code} {r.text}")
                errors += 1
                continue

            print(f"Imported activity {act.get('id')} as {r.json().get('id')}")
            imported += 1

    print(f"Done. Imported={imported}, skipped/failed={errors}")


if __name__ == "__main__":
    main()
