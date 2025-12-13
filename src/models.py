from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, JSON, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base
import enum
import uuid


class ExperimentStatus(enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()), primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    variant_assignments = relationship("UserVariantAssignment", back_populates="user")
    events = relationship("Event", back_populates="user")
    segment_assignments = relationship("UserSegment", back_populates="user")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Property-based rules stored as JSON
    # Example: {"is_premium": 1} or {"country_code": "US"}
    rules = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user_assignments = relationship("UserSegment", back_populates="segment")
    experiment_assignments = relationship("ExperimentSegment", back_populates="segment")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    variants = relationship("Variant", back_populates="experiment", cascade="all, delete-orphan")
    segment_assignments = relationship("ExperimentSegment", back_populates="experiment")


class Variant(Base):
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    name = Column(String, nullable=False)
    percent_allocated = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="variants")
    user_assignments = relationship("UserVariantAssignment", back_populates="variant")

    __table_args__ = (
        UniqueConstraint('experiment_id', 'name', name='uq_experiment_variant_name'),
    )


class UserVariantAssignment(Base):
    __tablename__ = "user_variant_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="variant_assignments")
    variant = relationship("Variant", back_populates="user_assignments")

    __table_args__ = (
        UniqueConstraint('user_id', 'experiment_id', name='uq_user_experiment'),
    )


class UserSegment(Base):
    __tablename__ = "user_segments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="segment_assignments")
    segment = relationship("Segment", back_populates="user_assignments")

    __table_args__ = (
        UniqueConstraint('user_id', 'segment_id', name='uq_user_segment'),
    )


class ExperimentSegment(Base):
    __tablename__ = "experiment_segments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="segment_assignments")
    segment = relationship("Segment", back_populates="experiment_assignments")

    __table_args__ = (
        UniqueConstraint('experiment_id', 'segment_id', name='uq_experiment_segment'),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=True)
    type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    properties = Column(JSON, nullable=True)

    user = relationship("User", back_populates="events")
