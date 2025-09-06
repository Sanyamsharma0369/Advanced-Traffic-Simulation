"""
Data models for the traffic control API.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union
from datetime import datetime
from enum import Enum


class TrafficLightPhase(str, Enum):
    """Traffic light phase enumeration."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    FLASHING = "flashing"


class VehicleType(str, Enum):
    """Vehicle type enumeration."""
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    EMERGENCY = "emergency"
    OTHER = "other"


class IntersectionStatus(BaseModel):
    """Intersection status model."""
    intersection_id: str
    current_phase: Dict[str, TrafficLightPhase]
    queue_lengths: Dict[str, int]
    waiting_times: Dict[str, float]
    vehicle_counts: Dict[str, int]
    timestamp: datetime = Field(default_factory=datetime.now)


class TrafficData(BaseModel):
    """Traffic data model for sensor inputs."""
    intersection_id: str
    approach_id: str
    vehicle_count: int
    queue_length: int
    average_speed: float
    timestamp: datetime = Field(default_factory=datetime.now)
    vehicle_types: Optional[Dict[VehicleType, int]] = None
    emergency_vehicle_present: bool = False


class PredictionRequest(BaseModel):
    """Request model for traffic prediction."""
    intersection_id: str
    historical_data: List[TrafficData]
    prediction_horizon: int = Field(default=10, description="Prediction horizon in minutes")
    include_weather: bool = False
    include_events: bool = False


class PredictionResponse(BaseModel):
    """Response model for traffic prediction."""
    intersection_id: str
    predicted_volumes: Dict[str, List[float]]
    predicted_queue_lengths: Dict[str, List[float]]
    timestamps: List[datetime]
    confidence: float


class OptimizationRequest(BaseModel):
    """Request model for signal timing optimization."""
    intersection_id: str
    traffic_volumes: Dict[str, float]
    queue_lengths: Dict[str, float]
    waiting_times: Dict[str, float]
    emergency_priority: Optional[Dict[str, float]] = None
    min_green_time: float = 10.0
    max_green_time: float = 120.0
    cycle_time_constraint: float = 180.0


class OptimizationResponse(BaseModel):
    """Response model for signal timing optimization."""
    intersection_id: str
    green_times: Dict[str, float]
    cycle_time: float
    phase_proportions: Dict[str, float]
    fitness: float
    timestamp: datetime = Field(default_factory=datetime.now)


class EmergencyVehicleDetection(BaseModel):
    """Emergency vehicle detection model."""
    intersection_id: str
    approach_id: str
    vehicle_type: VehicleType
    distance: float  # meters
    speed: float  # km/h
    estimated_arrival_time: float  # seconds
    timestamp: datetime = Field(default_factory=datetime.now)


class IntersectionConfiguration(BaseModel):
    """Intersection configuration model."""
    intersection_id: str
    name: str
    location: Dict[str, float]  # lat, lon
    approaches: List[str]
    phases: Dict[str, List[str]]  # phase_id -> list of approaches
    default_timing: Dict[str, float]  # phase_id -> default green time
    adjacent_intersections: List[str]
    is_active: bool = True


class WeatherData(BaseModel):
    """Weather data model."""
    intersection_id: str
    temperature: float
    precipitation: float
    visibility: float
    wind_speed: float
    road_condition: str
    timestamp: datetime = Field(default_factory=datetime.now)


class EventData(BaseModel):
    """Special event data model."""
    event_id: str
    name: str
    location: Dict[str, float]
    start_time: datetime
    end_time: datetime
    expected_attendance: int
    affected_intersections: List[str]


class SystemStatus(BaseModel):
    """System status model."""
    total_intersections: int
    active_intersections: int
    emergency_mode_intersections: int
    autonomous_mode_intersections: int
    system_health: str
    last_update: datetime = Field(default_factory=datetime.now)


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""
    intersection_id: str
    average_delay: float
    throughput: int
    congestion_reduction: float
    average_queue_length: float
    average_waiting_time: float
    emergency_response_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)