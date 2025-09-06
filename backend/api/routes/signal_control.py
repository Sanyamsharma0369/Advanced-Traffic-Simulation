"""
Signal Control API Routes
Handles traffic signal control operations including:
- Signal state changes
- Timing adjustments
- Emergency vehicle priority
- Green wave coordination
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from database.connectors.postgres_connector import PostgresConnector
from database.connectors.redis_connector import RedisConnector
from database.models.postgres_models import Signal, Intersection, SignalStatus

router = APIRouter(
    prefix="/signals",
    tags=["signal-control"],
    responses={404: {"description": "Not found"}},
)

# Initialize database connectors
postgres = PostgresConnector()
redis = RedisConnector()

@router.get("/intersections/{intersection_id}/status")
async def get_intersection_status(intersection_id: str):
    """
    Get current status of all signals at an intersection
    """
    # Check if status is in Redis cache first
    cached_status = redis.get_intersection_status(intersection_id)
    if cached_status:
        return cached_status
    
    # If not in cache, fetch from database
    try:
        with postgres.get_session() as session:
            signals = session.query(Signal).filter(Signal.intersection_id == intersection_id).all()
            
            if not signals:
                raise HTTPException(status_code=404, detail="Intersection not found")
                
            status = {
                "intersection_id": intersection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "signals": [
                    {
                        "id": signal.id,
                        "position": signal.position,
                        "status": signal.current_status.value,
                        "last_changed": signal.last_status_change.isoformat()
                    }
                    for signal in signals
                ]
            }
            
            # Cache the result
            redis.set_intersection_status(intersection_id, status, expiry=30)
            
            return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/intersections/{intersection_id}/signals/{signal_id}")
async def update_signal_status(
    intersection_id: str,
    signal_id: str,
    status: SignalStatus,
    background_tasks: BackgroundTasks
):
    """
    Update status of a specific signal
    """
    try:
        with postgres.get_session() as session:
            signal = session.query(Signal).filter(
                Signal.id == signal_id,
                Signal.intersection_id == intersection_id
            ).first()
            
            if not signal:
                raise HTTPException(status_code=404, detail="Signal not found")
                
            signal.current_status = status
            signal.last_status_change = datetime.utcnow()
            
            # Publish update to MQTT for edge devices
            background_tasks.add_task(
                publish_signal_change,
                intersection_id=intersection_id,
                signal_id=signal_id,
                status=status.value
            )
            
            # Invalidate cache
            redis.delete_key(f"intersection:{intersection_id}:status")
            
            return {
                "id": signal.id,
                "position": signal.position,
                "status": signal.current_status.value,
                "last_changed": signal.last_status_change.isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/intersections/{intersection_id}/timing")
async def update_timing_plan(
    intersection_id: str,
    timing_data: Dict[str, Any]
):
    """
    Update timing plan for an intersection
    """
    try:
        with postgres.get_session() as session:
            intersection = session.query(Intersection).filter(
                Intersection.id == intersection_id
            ).first()
            
            if not intersection:
                raise HTTPException(status_code=404, detail="Intersection not found")
                
            signals = session.query(Signal).filter(
                Signal.intersection_id == intersection_id
            ).all()
            
            for signal in signals:
                if signal.position in timing_data:
                    signal_timing = timing_data[signal.position]
                    signal.default_timing = signal_timing.get("default", signal.default_timing)
                    signal.min_timing = signal_timing.get("min", signal.min_timing)
                    signal.max_timing = signal_timing.get("max", signal.max_timing)
            
            # Publish timing updates to edge devices
            redis.publish_message(
                f"intersection:{intersection_id}:timing_update",
                timing_data
            )
            
            return {"message": "Timing plan updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/emergency-vehicle")
async def emergency_vehicle_priority(
    intersection_id: str,
    approach_direction: str,
    vehicle_type: str,
    eta_seconds: int,
    priority_level: int = Query(1, ge=1, le=3)
):
    """
    Handle emergency vehicle priority request
    """
    try:
        # Get current intersection status
        with postgres.get_session() as session:
            intersection = session.query(Intersection).filter(
                Intersection.id == intersection_id
            ).first()
            
            if not intersection:
                raise HTTPException(status_code=404, detail="Intersection not found")
        
        # Create emergency vehicle record in Redis
        emergency_id = str(uuid.uuid4())
        emergency_data = {
            "id": emergency_id,
            "intersection_id": intersection_id,
            "approach_direction": approach_direction,
            "vehicle_type": vehicle_type,
            "eta_seconds": eta_seconds,
            "priority_level": priority_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis with expiration
        redis.set_value(
            f"emergency:{emergency_id}",
            emergency_data,
            expiry=eta_seconds + 60  # Add buffer time
        )
        
        # Publish to emergency channel
        redis.publish_message(
            "emergency_vehicle_priority",
            emergency_data
        )
        
        return {
            "emergency_id": emergency_id,
            "status": "priority_requested",
            "eta_seconds": eta_seconds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/green-wave")
async def coordinate_green_wave(
    corridor_id: str,
    direction: str,
    speed_kph: float,
    intersections: List[str],
    start_time: Optional[datetime] = None
):
    """
    Coordinate green wave along a corridor
    """
    if not start_time:
        start_time = datetime.utcnow()
        
    try:
        # Validate intersections exist
        with postgres.get_session() as session:
            for intersection_id in intersections:
                intersection = session.query(Intersection).filter(
                    Intersection.id == intersection_id
                ).first()
                
                if not intersection:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Intersection {intersection_id} not found"
                    )
        
        # Create green wave coordination plan
        green_wave_id = str(uuid.uuid4())
        green_wave_data = {
            "id": green_wave_id,
            "corridor_id": corridor_id,
            "direction": direction,
            "speed_kph": speed_kph,
            "intersections": intersections,
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        # Store in Redis
        redis.set_value(
            f"green_wave:{green_wave_id}",
            green_wave_data,
            expiry=3600  # 1 hour expiry
        )
        
        # Publish to coordination channel
        redis.publish_message(
            "green_wave_coordination",
            green_wave_data
        )
        
        return {
            "green_wave_id": green_wave_id,
            "status": "scheduled",
            "intersections": len(intersections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

async def publish_signal_change(intersection_id: str, signal_id: str, status: str):
    """
    Publish signal change to MQTT broker for edge devices
    """
    message = {
        "intersection_id": intersection_id,
        "signal_id": signal_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # This would typically use an MQTT client
    # For now, we'll use Redis pub/sub as a placeholder
    redis.publish_message(f"intersection:{intersection_id}:signal_change", message)