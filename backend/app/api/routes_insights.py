from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.insight import InsightRead
from app.services.insight_service import get_insight

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/{insight_id}", response_model=InsightRead)
def get_insight_by_id(insight_id: UUID, db: Session = Depends(get_db)):
    insight = get_insight(db, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight
