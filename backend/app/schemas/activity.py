from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RoutePoint(BaseModel):
    lat: float
    lon: float


class ActivityBase(BaseModel):
    user_id: UUID
    external_id: str
    source: str = Field(example="strava")
    start_time: datetime
    duration_seconds: int
    distance_meters: int
    avg_heart_rate: Optional[int]
    route: List[RoutePoint]


class ActivityCreate(ActivityBase):
    pass


class ActivityRead(BaseModel):
    id: UUID
    user_id: UUID
    external_id: str
    source: str
    start_time: datetime
    duration_seconds: int
    distance_meters: int
    avg_heart_rate: Optional[int]

    class Config:
        orm_mode = True


class ActivityNearbyQuery(BaseModel):
    lat: float
    lon: float
    radius_meters: int = 1000
