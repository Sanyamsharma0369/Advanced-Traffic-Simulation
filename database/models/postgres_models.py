"""
PostgreSQL data models for Smart Traffic Light Controller System
Uses SQLAlchemy ORM for database interactions
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

Base = declarative_base()

class SignalStatus(enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    FLASHING = "flashing"
    OFF = "off"

class IntersectionType(enum.Enum):
    FOUR_WAY = "four_way"
    THREE_WAY = "three_way"
    ROUNDABOUT = "roundabout"
    COMPLEX = "complex"

class Intersection(Base):
    """Intersection configuration and metadata"""
    __tablename__ = "intersections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    type = Column(Enum(IntersectionType), nullable=False)
    lanes_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    config = Column(JSON)  # Stores complex configuration as JSON
    
    # Relationships
    signals = relationship("Signal", back_populates="intersection")
    sensors = relationship("Sensor", back_populates="intersection")

class Signal(Base):
    """Traffic signal configuration"""
    __tablename__ = "signals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    intersection_id = Column(String(36), ForeignKey("intersections.id"), nullable=False)
    position = Column(String(50), nullable=False)  # e.g., "north_bound", "east_left"
    default_timing = Column(Integer, nullable=False)  # Default timing in seconds
    min_timing = Column(Integer, nullable=False)
    max_timing = Column(Integer, nullable=False)
    current_status = Column(Enum(SignalStatus), default=SignalStatus.RED)
    last_status_change = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    intersection = relationship("Intersection", back_populates="signals")
    timing_plans = relationship("TimingPlan", back_populates="signal")

class Sensor(Base):
    """Traffic sensors at intersections"""
    __tablename__ = "sensors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    intersection_id = Column(String(36), ForeignKey("intersections.id"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "camera", "induction_loop"
    position = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    last_maintenance = Column(DateTime, default=datetime.utcnow)
    firmware_version = Column(String(50))
    
    # Relationships
    intersection = relationship("Intersection", back_populates="sensors")

class TimingPlan(Base):
    """Signal timing plans for different scenarios"""
    __tablename__ = "timing_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(36), ForeignKey("signals.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    time_of_day_start = Column(Integer)  # Minutes from midnight
    time_of_day_end = Column(Integer)    # Minutes from midnight
    weekday_mask = Column(Integer)       # Bitmask for days of week
    green_time = Column(Integer, nullable=False)
    yellow_time = Column(Integer, nullable=False)
    red_time = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Relationships
    signal = relationship("Signal", back_populates="timing_plans")

class User(Base):
    """System users"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSettings(Base):
    """Global system settings"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(255))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(36), ForeignKey("users.id"))

class OptimizationRun(Base):
    """Records of optimization algorithm runs"""
    __tablename__ = "optimization_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    algorithm = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20), default="running")
    parameters = Column(JSON)
    results = Column(JSON)
    created_by = Column(String(36), ForeignKey("users.id"))