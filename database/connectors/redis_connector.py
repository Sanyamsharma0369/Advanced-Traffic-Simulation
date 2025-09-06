"""
Redis Connector for Smart Traffic Light Controller System
Handles caching, pub/sub, and real-time data operations
"""
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
import redis

from database.config.database_config import REDIS_CONFIG

logger = logging.getLogger(__name__)

class RedisConnector:
    """Connector for Redis operations including caching and pub/sub"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.config = REDIS_CONFIG
        self.redis = redis.Redis(
            host=self.config["host"],
            port=self.config["port"],
            db=self.config["db"],
            password=self.config["password"],
            decode_responses=self.config["decode_responses"],
            socket_timeout=self.config["socket_timeout"]
        )
        self.pubsub = self.redis.pubsub()
        
    def set_value(self, key: str, value: Union[str, Dict, List], 
                 expiry: Optional[int] = None) -> bool:
        """
        Set a value in Redis with optional expiration
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if dict or list)
            expiry: Optional expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
                
            if expiry:
                return bool(self.redis.setex(key, expiry, value))
            else:
                return bool(self.redis.set(key, value))
        except redis.RedisError as e:
            logger.error(f"Error setting Redis value: {e}")
            return False
            
    def get_value(self, key: str, deserialize: bool = True) -> Any:
        """
        Get a value from Redis
        
        Args:
            key: Redis key
            deserialize: Whether to attempt JSON deserialization
            
        Returns:
            Value if found, None otherwise
        """
        try:
            value = self.redis.get(key)
            
            if value and deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        except redis.RedisError as e:
            logger.error(f"Error getting Redis value: {e}")
            return None
            
    def delete_key(self, key: str) -> bool:
        """
        Delete a key from Redis
        
        Args:
            key: Redis key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.error(f"Error deleting Redis key: {e}")
            return False
            
    def publish_message(self, channel: str, message: Union[str, Dict, List]) -> bool:
        """
        Publish a message to a Redis channel
        
        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized if dict or list)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
                
            return bool(self.redis.publish(channel, message))
        except redis.RedisError as e:
            logger.error(f"Error publishing Redis message: {e}")
            return False
            
    def subscribe(self, channels: List[str]) -> None:
        """
        Subscribe to Redis channels
        
        Args:
            channels: List of channel names
        """
        try:
            self.pubsub.subscribe(*channels)
        except redis.RedisError as e:
            logger.error(f"Error subscribing to Redis channels: {e}")
            
    def listen_for_messages(self, callback: Callable[[str, str], None], 
                           timeout: float = 0.01) -> None:
        """
        Listen for messages on subscribed channels
        
        Args:
            callback: Function to call with (channel, message) when message received
            timeout: Timeout for listening in seconds
        """
        try:
            message = self.pubsub.get_message(timeout=timeout)
            if message and message["type"] == "message":
                channel = message["channel"]
                data = message["data"]
                
                try:
                    # Attempt to deserialize JSON
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    pass
                    
                callback(channel, data)
        except redis.RedisError as e:
            logger.error(f"Error listening for Redis messages: {e}")
            
    def get_intersection_status(self, intersection_id: str) -> Dict[str, Any]:
        """
        Get current status for a specific intersection
        
        Args:
            intersection_id: ID of the intersection
            
        Returns:
            Dictionary with intersection status
        """
        key = f"intersection:{intersection_id}:status"
        return self.get_value(key, deserialize=True) or {}
        
    def set_intersection_status(self, intersection_id: str, 
                              status: Dict[str, Any], 
                              expiry: int = 300) -> bool:
        """
        Set current status for a specific intersection
        
        Args:
            intersection_id: ID of the intersection
            status: Status dictionary
            expiry: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        key = f"intersection:{intersection_id}:status"
        return self.set_value(key, status, expiry)
        
    def close(self) -> None:
        """Close Redis connection"""
        try:
            self.pubsub.close()
            self.redis.close()
        except redis.RedisError as e:
            logger.error(f"Error closing Redis connection: {e}")