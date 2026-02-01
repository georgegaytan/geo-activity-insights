from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class InsightCreate(BaseModel):
    activity_id: UUID


class InsightRead(BaseModel):
    id: UUID
    activity_id: UUID
    status: str
    summary: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
