import json
import os
from typing import Optional
from uuid import UUID

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import InsightReport


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_KEY = os.getenv("INSIGHT_QUEUE_KEY", "insight_jobs")


def _get_redis() -> redis.Redis:
    return redis.from_url(REDIS_URL)


def enqueue_insight_job(report_id: UUID) -> None:
    r = _get_redis()
    job = {"insight_id": str(report_id)}
    r.rpush(QUEUE_KEY, json.dumps(job))


def get_insight(db: Session, insight_id: UUID) -> Optional[InsightReport]:
    return db.scalars(
        select(InsightReport).where(InsightReport.id == insight_id)
    ).one_or_none()
