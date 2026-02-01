from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import Activity
from app.db.session import get_db
from app.schemas.activity import ActivityNearbyQuery, ActivityRead
from app.schemas.insight import InsightRead
from app.services.activity_service import create_insight_report, find_activities_nearby, list_activities
from app.services.insight_service import enqueue_insight_job

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/", response_model=List[ActivityRead])
def get_activities(db: Session = Depends(get_db)):
    activities = list_activities(db)
    return activities


@router.get("/nearby", response_model=List[ActivityRead])
def get_activities_nearby(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_meters: int = Query(1000, ge=1),
    db: Session = Depends(get_db),
):
    query = ActivityNearbyQuery(lat=lat, lon=lon, radius_meters=radius_meters)
    activities = find_activities_nearby(db, query.lat, query.lon, query.radius_meters)
    return activities


@router.post("/{activity_id}/generate-insight", response_model=InsightRead, status_code=status.HTTP_201_CREATED)
def generate_insight_for_activity(activity_id: UUID, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    report = create_insight_report(db, activity_id)
    enqueue_insight_job(report.id)
    return report
