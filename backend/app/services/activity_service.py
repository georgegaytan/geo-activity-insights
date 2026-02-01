from datetime import datetime
from typing import Iterable, List, Optional
from uuid import UUID

from geoalchemy2.shape import from_shape
from shapely.geometry import LineString
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Activity, InsightReport, InsightStatusEnum
from app.schemas.activity import ActivityCreate


def _route_to_linestring(route_points: Iterable[dict]) -> LineString:
    coords = [(p["lon"], p["lat"]) for p in route_points]
    return LineString(coords)


def upsert_activity_from_webhook(db: Session, payload: dict) -> Activity:
    activity_data = ActivityCreate(**payload)

    existing: Optional[Activity] = db.execute(
        select(Activity).where(Activity.external_id == activity_data.external_id)
    ).scalar_one_or_none()

    line = _route_to_linestring([p.dict() for p in activity_data.route])
    geo = from_shape(line, srid=4326)

    if existing:
        existing.user_id = activity_data.user_id
        existing.source = activity_data.source
        existing.start_time = activity_data.start_time
        existing.duration_seconds = activity_data.duration_seconds
        existing.distance_meters = activity_data.distance_meters
        existing.avg_heart_rate = activity_data.avg_heart_rate
        existing.route = geo
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    activity = Activity(
        user_id=activity_data.user_id,
        external_id=activity_data.external_id,
        source=activity_data.source,
        start_time=activity_data.start_time,
        duration_seconds=activity_data.duration_seconds,
        distance_meters=activity_data.distance_meters,
        avg_heart_rate=activity_data.avg_heart_rate,
        route=geo,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_activities(db: Session) -> List[Activity]:
    return list(db.execute(select(Activity).order_by(Activity.start_time.desc())).scalars())


def find_activities_nearby(db: Session, lat: float, lon: float, radius_meters: int) -> List[Activity]:
    point_wkt = f"POINT({lon} {lat})"
    stmt = (
        select(Activity)
        .where(
            func.ST_DWithin(
                Activity.route,
                func.ST_GeogFromText(point_wkt),
                radius_meters,
            )
        )
        .order_by(Activity.start_time.desc())
    )
    return list(db.execute(stmt).scalars())


def create_insight_report(db: Session, activity_id: UUID) -> InsightReport:
    report = InsightReport(
        activity_id=activity_id,
        status=InsightStatusEnum.PENDING,
        created_at=datetime.now(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
