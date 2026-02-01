import json
import os
import time
from datetime import datetime, timedelta
from typing import List

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Activity, InsightReport, InsightStatusEnum
from app.db.session import SessionLocal


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_KEY = os.getenv("INSIGHT_QUEUE_KEY", "insight_jobs")
POLL_INTERVAL_SECONDS = int(os.getenv("WORKER_POLL_INTERVAL", "2"))


def _get_redis() -> redis.Redis:
    return redis.from_url(REDIS_URL)


def _mock_llm_call(activity: Activity, recent_activities: List[Activity]) -> str:
    recent_count = len(recent_activities)
    avg_distance = 0
    if recent_activities:
        avg_distance = sum(a.distance_meters for a in recent_activities) / recent_count

    summary = (
        f"Workout on {activity.start_time.date()} from source {activity.source}. "
        f"Duration: {activity.duration_seconds // 60} min, distance: {activity.distance_meters / 1000:.1f} km. "
        f"Average HR: {activity.avg_heart_rate or 'n/a'}. "
        f"You have completed {recent_count} activities in the last 7 days with an average distance of "
        f"{avg_distance / 1000:.1f} km."
    )
    return summary


def process_insight_job(session: Session, insight_id: str) -> None:
    report: InsightReport | None = session.get(InsightReport, insight_id)
    if not report:
        return

    report.status = InsightStatusEnum.PROCESSING
    session.add(report)
    session.commit()

    activity: Activity | None = session.get(Activity, report.activity_id)
    if not activity:
        report.status = InsightStatusEnum.FAILED
        session.add(report)
        session.commit()
        return

    one_week_ago = datetime.now() - timedelta(days=7)
    recent_activities = list(
        session.execute(
            select(Activity).where(
                Activity.user_id == activity.user_id,
                Activity.start_time >= one_week_ago,
            )
        ).scalars()
    )

    # Simulate a call to an external LLM provider
    summary = _mock_llm_call(activity, recent_activities)

    report.summary = summary
    report.status = InsightStatusEnum.DONE
    session.add(report)
    session.commit()


def run_worker() -> None:
    r = _get_redis()
    print("Insight worker started, waiting for jobs...")

    while True:
        try:
            job_data = r.lpop(QUEUE_KEY)
            if not job_data:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            job = json.loads(job_data)
            insight_id = job.get("insight_id")
            if not insight_id:
                continue

            with SessionLocal() as session:
                process_insight_job(session, insight_id)
        except Exception as exc:  # pragma: no cover - log and continue
            print(f"Worker error: {exc}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_worker()
