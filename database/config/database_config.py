"""
Database Configuration for Smart Traffic Light Controller System
Handles connection settings for PostgreSQL, InfluxDB, and Redis
"""
import os
from typing import Dict, Any

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    "database": os.environ.get("POSTGRES_DB", "traffic_control"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
    "min_connections": int(os.environ.get("POSTGRES_MIN_CONN", 5)),
    "max_connections": int(os.environ.get("POSTGRES_MAX_CONN", 20)),
}

# InfluxDB Configuration for time-series data
INFLUXDB_CONFIG = {
    "url": os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
    "token": os.environ.get("INFLUXDB_TOKEN", "traffic_token"),
    "org": os.environ.get("INFLUXDB_ORG", "traffic_org"),
    "bucket": os.environ.get("INFLUXDB_BUCKET", "traffic_metrics"),
    "retention_period": os.environ.get("INFLUXDB_RETENTION", "30d"),
}

# Redis Configuration for caching and pub/sub
REDIS_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "localhost"),
    "port": int(os.environ.get("REDIS_PORT", 6379)),
    "db": int(os.environ.get("REDIS_DB", 0)),
    "password": os.environ.get("REDIS_PASSWORD", None),
    "decode_responses": True,
    "socket_timeout": 5,
}

# Database selection for different data types
DATA_STORAGE_MAPPING = {
    "intersection_config": "postgres",  # Static configuration data
    "traffic_signals": "postgres",      # Signal configurations
    "user_accounts": "postgres",        # User authentication and permissions
    "system_settings": "postgres",      # System-wide settings
    
    "traffic_metrics": "influxdb",      # Time-series traffic data
    "sensor_readings": "influxdb",      # Raw sensor data
    "performance_metrics": "influxdb",  # System performance metrics
    
    "current_status": "redis",          # Real-time intersection status
    "active_signals": "redis",          # Current signal states
    "emergency_vehicles": "redis",      # Active emergency vehicle data
}

def get_db_config(db_type: str) -> Dict[str, Any]:
    """
    Get configuration for specified database type
    
    Args:
        db_type: One of 'postgres', 'influxdb', or 'redis'
        
    Returns:
        Dict containing configuration parameters
    """
    if db_type.lower() == 'postgres':
        return POSTGRES_CONFIG
    elif db_type.lower() == 'influxdb':
        return INFLUXDB_CONFIG
    elif db_type.lower() == 'redis':
        return REDIS_CONFIG
    else:
        raise ValueError(f"Unknown database type: {db_type}")