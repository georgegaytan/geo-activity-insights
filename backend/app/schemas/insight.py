from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InsightCreate(BaseModel):
    activity_id: UUID


class InsightRead(BaseModel):
    id: UUID
    activity_id: UUID
    status: str
    summary: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
