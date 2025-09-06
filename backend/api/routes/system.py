"""
System API Routes
Handles system settings, configuration, and management
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from database.connectors.postgres_connector import PostgresConnector
from database.connectors.redis_connector import RedisConnector
from database.models.postgres_models import SystemSettings, User

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}},
)

# Initialize database connectors
postgres = PostgresConnector()
redis = RedisConnector()

class SystemSettingsModel(BaseModel):
    ml_model_type: str
    optimization_algorithm: str
    emergency_vehicle_priority: bool
    green_wave_coordination: bool
    data_retention_days: int
    api_endpoint: Optional[str] = None
    notification_email: Optional[str] = None

class UserModel(BaseModel):
    username: str
    email: str
    role: str
    password: Optional[str] = None

@router.get("/settings")
async def get_system_settings():
    """
    Get current system settings
    """
    try:
        # Try to get from Redis cache first
        cached_settings = redis.get("system:settings")
        if cached_settings:
            return cached_settings
            
        # If not in cache, get from PostgreSQL
        with postgres.get_session() as session:
            settings = session.query(SystemSettings).order_by(SystemSettings.created_at.desc()).first()
            
            if not settings:
                raise HTTPException(status_code=404, detail="System settings not found")
                
            # Cache the settings
            settings_dict = {
                "id": settings.id,
                "ml_model_type": settings.ml_model_type,
                "optimization_algorithm": settings.optimization_algorithm,
                "emergency_vehicle_priority": settings.emergency_vehicle_priority,
                "green_wave_coordination": settings.green_wave_coordination,
                "data_retention_days": settings.data_retention_days,
                "api_endpoint": settings.api_endpoint,
                "notification_email": settings.notification_email,
                "created_at": settings.created_at.isoformat(),
                "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
            }
            
            redis.set("system:settings", settings_dict, expire=3600)  # Cache for 1 hour
            
            return settings_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system settings: {str(e)}")

@router.post("/settings")
async def update_system_settings(settings: SystemSettingsModel):
    """
    Update system settings
    """
    try:
        with postgres.get_session() as session:
            # Create new settings record
            new_settings = SystemSettings(
                ml_model_type=settings.ml_model_type,
                optimization_algorithm=settings.optimization_algorithm,
                emergency_vehicle_priority=settings.emergency_vehicle_priority,
                green_wave_coordination=settings.green_wave_coordination,
                data_retention_days=settings.data_retention_days,
                api_endpoint=settings.api_endpoint,
                notification_email=settings.notification_email,
                created_at=datetime.utcnow()
            )
            
            session.add(new_settings)
            session.commit()
            
            # Update Redis cache
            settings_dict = {
                "id": new_settings.id,
                "ml_model_type": new_settings.ml_model_type,
                "optimization_algorithm": new_settings.optimization_algorithm,
                "emergency_vehicle_priority": new_settings.emergency_vehicle_priority,
                "green_wave_coordination": new_settings.green_wave_coordination,
                "data_retention_days": new_settings.data_retention_days,
                "api_endpoint": new_settings.api_endpoint,
                "notification_email": new_settings.notification_email,
                "created_at": new_settings.created_at.isoformat(),
                "updated_at": new_settings.updated_at.isoformat() if new_settings.updated_at else None
            }
            
            redis.set("system:settings", settings_dict, expire=3600)  # Cache for 1 hour
            
            # Publish settings update event
            redis.publish("system:events", {
                "type": "settings_updated",
                "data": settings_dict
            })
            
            return {
                "status": "success",
                "message": "System settings updated successfully",
                "settings": settings_dict
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating system settings: {str(e)}")

@router.get("/health")
async def health_check():
    """
    System health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check PostgreSQL
    try:
        with postgres.get_session() as session:
            session.execute("SELECT 1")
        health_status["components"]["postgres"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["postgres"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis.set("health:check", "ok", expire=10)
        value = redis.get("health:check")
        if value == "ok":
            health_status["components"]["redis"] = {"status": "healthy"}
        else:
            health_status["components"]["redis"] = {"status": "unhealthy", "error": "Value mismatch"}
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check InfluxDB (via Redis cache)
    try:
        influx_status = redis.get("health:influxdb")
        if influx_status and influx_status.get("status") == "healthy":
            health_status["components"]["influxdb"] = {"status": "healthy"}
        else:
            health_status["components"]["influxdb"] = {"status": "unknown"}
    except Exception:
        health_status["components"]["influxdb"] = {"status": "unknown"}
    
    return health_status

@router.get("/users")
async def get_users():
    """
    Get all system users
    """
    try:
        with postgres.get_session() as session:
            users = session.query(User).all()
            
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                })
                
            return user_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")

@router.post("/users")
async def create_user(user: UserModel):
    """
    Create a new system user
    """
    try:
        with postgres.get_session() as session:
            # Check if username already exists
            existing_user = session.query(User).filter(User.username == user.username).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")
                
            # Create new user
            new_user = User(
                username=user.username,
                email=user.email,
                role=user.role,
                created_at=datetime.utcnow()
            )
            
            if user.password:
                # In a real system, you would hash the password here
                new_user.password_hash = f"hashed_{user.password}"
                
            session.add(new_user)
            session.commit()
            
            return {
                "status": "success",
                "message": "User created successfully",
                "user": {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "role": new_user.role,
                    "created_at": new_user.created_at.isoformat()
                }
            }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    """
    Get system logs
    """
    try:
        # In a real system, you would query logs from a logging system
        # Here we'll simulate some logs
        
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "System started successfully",
                "component": "main"
            },
            {
                "timestamp": (datetime.utcnow() - datetime.timedelta(minutes=5)).isoformat(),
                "level": "WARNING",
                "message": "High traffic detected at intersection ID-001",
                "component": "traffic_monitor"
            },
            {
                "timestamp": (datetime.utcnow() - datetime.timedelta(minutes=10)).isoformat(),
                "level": "ERROR",
                "message": "Failed to connect to sensor S-123",
                "component": "sensor_manager"
            }
        ]
        
        # Filter by level if provided
        if level:
            logs = [log for log in logs if log["level"].lower() == level.lower()]
            
        return {
            "logs": logs,
            "count": len(logs),
            "filters": {
                "level": level,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system logs: {str(e)}")

@router.post("/backup")
async def create_system_backup():
    """
    Create a system backup
    """
    try:
        # In a real system, you would trigger a backup process
        # Here we'll simulate a backup
        
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "status": "success",
            "message": "System backup initiated",
            "backup_id": backup_id,
            "estimated_completion_time": (datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating system backup: {str(e)}")

@router.post("/restore/{backup_id}")
async def restore_system_backup(backup_id: str):
    """
    Restore system from backup
    """
    try:
        # In a real system, you would trigger a restore process
        # Here we'll simulate a restore
        
        return {
            "status": "success",
            "message": f"System restore from backup {backup_id} initiated",
            "estimated_completion_time": (datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring system from backup: {str(e)}")