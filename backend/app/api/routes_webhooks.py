from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.activity import ActivityCreate
from app.services.activity_service import upsert_activity_from_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/strava", status_code=status.HTTP_201_CREATED)
def receive_strava_webhook(payload: ActivityCreate, db: Session = Depends(get_db)):
    try:
        activity = upsert_activity_from_webhook(db, payload.dict())
    except Exception as exc:  # pragma: no cover - generic safety
        raise HTTPException(status_code=400, detail=str(exc))
    return {"id": str(activity.id), "external_id": activity.external_id}
