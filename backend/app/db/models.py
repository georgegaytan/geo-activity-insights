import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)

    activities = relationship("Activity", back_populates="user")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    external_id = Column(String, unique=True, nullable=False, index=True)
    source = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    distance_meters = Column(Integer, nullable=False)
    avg_heart_rate = Column(Integer, nullable=True)
    route = Column(Geography(geometry_type="LINESTRING", srid=4326), nullable=False)

    user = relationship("User", back_populates="activities")
    insights = relationship("InsightReport", back_populates="activity")


class InsightStatusEnum(str):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class InsightReport(Base):
    __tablename__ = "insight_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default=InsightStatusEnum.PENDING)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)

    activity = relationship("Activity", back_populates="insights")
