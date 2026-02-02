from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


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
    avg_heart_rate: Optional[Union[int, float]]
    route: List[RoutePoint]

    @field_validator('avg_heart_rate', mode='before')
    @classmethod
    def coerce_avg_heart_rate(cls, v):
        if v is None:
            return None
        # Accept both int and float, but store as int (rounded)
        return int(round(v))


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

    model_config = ConfigDict(from_attributes=True)


class ActivityNearbyQuery(BaseModel):
    lat: float
    lon: float
    radius_meters: int = 1000
