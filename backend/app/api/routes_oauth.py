import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StravaAccount
from app.db.session import get_db
from app.services.strava_service import import_recent_activities, upsert_strava_account

router = APIRouter(tags=["strava-oauth"])


@router.get("/strava/oauth/callback", response_class=HTMLResponse)
async def strava_oauth_callback(
    code: str = Query(..., description="Authorization code returned by Strava"),
    scope: str | None = Query(None),
    state: str | None = Query(None),
):
    # For now we just display the code so you can copy it and exchange it for a token
    html = f"""
    <html>
      <head><title>Strava OAuth Callback</title></head>
      <body style="font-family: system-ui, sans-serif; padding: 2rem;">
        <h1>Strava Authorization Received</h1>
        <p><strong>Authorization code:</strong></p>
        <pre style="background:#f5f5f5;padding:1rem;border-radius:4px;">{code}</pre>
        <p>You can now use this code to exchange for an access token using the Strava API, or call the /strava/oauth/exchange endpoint with this code.</p>
        <h2>Additional Parameters</h2>
        <ul>
          <li><strong>scope</strong>: {scope or "(none)"}</li>
          <li><strong>state</strong>: {state or "(none)"}</li>
        </ul>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


class StravaCodePayload(BaseModel):
    code: str


@router.post("/strava/oauth/exchange")
async def strava_oauth_exchange(payload: StravaCodePayload, db: Session = Depends(get_db)):
    """Exchange a Strava authorization code for an access/refresh token.

    Expects STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET in the environment.
    Returns the JSON payload from Strava on success.
    """

    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be configured in the environment.",
        )

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": payload.code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://www.strava.com/oauth/token", data=data)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail={"message": "Failed to exchange code with Strava", "response": resp.json()},
        )

    token_payload = resp.json()
    account = upsert_strava_account(db, token_payload)

    return {"account_id": str(account.id), "athlete_id": account.athlete_id, "token": token_payload}


class StravaImportRequest(BaseModel):
    athlete_id: int | None = None
    per_page: int = 10


@router.post("/strava/import-activities")
async def strava_import_activities(payload: StravaImportRequest, db: Session = Depends(get_db)):
    """Import recent activities from Strava into the local Activity table."""

    stmt = select(StravaAccount)
    if payload.athlete_id is not None:
        stmt = stmt.where(StravaAccount.athlete_id == payload.athlete_id)

    account = db.scalars(stmt).one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Strava account not found")

    imported = await import_recent_activities(db, account, per_page=payload.per_page)
    return {"imported": imported}
