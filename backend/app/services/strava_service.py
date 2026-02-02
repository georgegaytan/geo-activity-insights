from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Activity, StravaAccount, User
from app.services.activity_service import upsert_activity_from_webhook


STRAVA_API_BASE = "https://www.strava.com/api/v3"


def upsert_strava_account(db: Session, token_payload: Dict[str, Any]) -> StravaAccount:
    athlete = token_payload["athlete"]
    athlete_id = int(athlete["id"])

    existing: StravaAccount | None = db.scalars(
        select(StravaAccount).where(StravaAccount.athlete_id == athlete_id)
    ).one_or_none()

    if existing:
        existing.access_token = token_payload["access_token"]
        existing.refresh_token = token_payload["refresh_token"]
        existing.expires_at = int(token_payload["expires_at"])
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    # Create a synthetic user for this Strava athlete if one does not exist yet
    email = f"strava_{athlete_id}@example.com"
    user = db.scalars(select(User).where(User.email == email)).one_or_none()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    account = StravaAccount(
        user_id=user.id,
        athlete_id=athlete_id,
        access_token=token_payload["access_token"],
        refresh_token=token_payload["refresh_token"],
        expires_at=int(token_payload["expires_at"]),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


async def _ensure_valid_access_token(db: Session, account: StravaAccount) -> StravaAccount:
    """Refresh access token if expired. For now we refresh when expired or about to expire."""

    if account.expires_at > int(time.time()) + 60:
        return account

    client_id = os.getenv("STRAVA_CLIENT_ID")
    if not client_id:
        raise RuntimeError("STRAVA_CLIENT_ID must be set in the environment to refresh Strava tokens")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": account.refresh_token,
            },
        )

    resp.raise_for_status()
    data = resp.json()

    account.access_token = data["access_token"]
    account.refresh_token = data["refresh_token"]
    account.expires_at = int(data["expires_at"])
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


async def import_recent_activities(db: Session, account: StravaAccount, per_page: int = 10) -> int:
    """Fetch recent Strava activities and upsert them into our Activity table.

    Returns the number of activities imported/updated.
    """

    account = await _ensure_valid_access_token(db, account)

    headers = {"Authorization": f"Bearer {account.access_token}"}
    params = {"per_page": per_page, "page": 1}

    async with httpx.AsyncClient(base_url=STRAVA_API_BASE, headers=headers) as client:
        resp = await client.get("/athlete/activities", params=params)
    resp.raise_for_status()
    activities: List[Dict[str, Any]] = resp.json()

    imported = 0
    for item in activities:
        # Use Strava activity ID as our external_id
        external_id = f"strava-{item['id']}"

        # Build a simple route from start/end latlng if available
        start = item.get("start_latlng")
        end = item.get("end_latlng") or start
        if not start:
            # Skip activities without location for this prototype
            continue

        route = [
            {"lat": start[0], "lon": start[1]},
        ]
        if end and end != start:
            route.append({"lat": end[0], "lon": end[1]})

        payload = {
            "user_id": str(account.user_id),
            "external_id": external_id,
            "source": "strava",
            "start_time": item["start_date"],
            "duration_seconds": item["elapsed_time"],
            "distance_meters": int(item["distance"]),
            "avg_heart_rate": item.get("average_heartrate"),
            "route": route,
        }

        upsert_activity_from_webhook(db, payload)
        imported += 1

    return imported
