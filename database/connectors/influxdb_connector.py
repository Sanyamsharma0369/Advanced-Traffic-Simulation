"""
InfluxDB Connector for Smart Traffic Light Controller System
Handles time-series data storage and retrieval
"""
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError

from database.config.database_config import INFLUXDB_CONFIG

logger = logging.getLogger(__name__)

class InfluxDBConnector:
    """Connector for InfluxDB time-series database operations"""
    
    def __init__(self, async_mode: bool = False):
        """
        Initialize InfluxDB client
        
        Args:
            async_mode: If True, use asynchronous write mode
        """
        self.config = INFLUXDB_CONFIG
        self.client = InfluxDBClient(
            url=self.config["url"],
            token=self.config["token"],
            org=self.config["org"]
        )
        self.write_api = self.client.write_api(
            write_options=ASYNCHRONOUS if async_mode else SYNCHRONOUS
        )
        self.query_api = self.client.query_api()
        self.bucket = self.config["bucket"]
        
    def write_data_point(self, measurement: str, tags: Dict[str, str], 
                        fields: Dict[str, Union[float, int, str, bool]], 
                        timestamp: Optional[datetime] = None) -> bool:
        """
        Write a single data point to InfluxDB
        
        Args:
            measurement: Name of the measurement
            tags: Dictionary of tags
            fields: Dictionary of fields
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            point = Point(measurement)
            
            # Add tags
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)
                
            # Add fields
            for field_key, field_value in fields.items():
                point = point.field(field_key, field_value)
                
            # Set timestamp if provided
            if timestamp:
                point = point.time(timestamp, WritePrecision.NS)
                
            self.write_api.write(bucket=self.bucket, record=point)
            return True
        except InfluxDBError as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False
    
    def write_batch(self, points: List[Point]) -> bool:
        """
        Write multiple data points in batch
        
        Args:
            points: List of Point objects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.write_api.write(bucket=self.bucket, record=points)
            return True
        except InfluxDBError as e:
            logger.error(f"Error batch writing to InfluxDB: {e}")
            return False
    
    def query_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a Flux query against InfluxDB
        
        Args:
            query: Flux query string
            
        Returns:
            List of result records
        """
        try:
            tables = self.query_api.query(query, org=self.config["org"])
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "measurement": record.get_measurement(),
                        **record.values
                    })
            return results
        except InfluxDBError as e:
            logger.error(f"Error querying InfluxDB: {e}")
            return []
    
    def get_traffic_metrics(self, intersection_id: str, start_time: datetime, 
                           end_time: Optional[datetime] = None, 
                           aggregation: str = "mean") -> List[Dict[str, Any]]:
        """
        Get traffic metrics for a specific intersection
        
        Args:
            intersection_id: ID of the intersection
            start_time: Start time for the query
            end_time: End time for the query (defaults to current time)
            aggregation: Aggregation function (mean, max, min, sum)
            
        Returns:
            List of traffic metrics
        """
        if not end_time:
            end_time = datetime.utcnow()
            
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "traffic_metrics")
            |> filter(fn: (r) => r.intersection_id == "{intersection_id}")
            |> {aggregation}()
        '''
        
        return self.query_data(query)
    
    def get_sensor_readings(self, sensor_id: str, start_time: datetime,
                           end_time: Optional[datetime] = None,
                           limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get sensor readings for a specific sensor
        
        Args:
            sensor_id: ID of the sensor
            start_time: Start time for the query
            end_time: End time for the query (defaults to current time)
            limit: Maximum number of readings to return
            
        Returns:
            List of sensor readings
        """
        if not end_time:
            end_time = datetime.utcnow()
            
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "sensor_readings")
            |> filter(fn: (r) => r.sensor_id == "{sensor_id}")
            |> limit(n: {limit})
        '''
        
        return self.query_data(query)
    
    def close(self):
        """Close the InfluxDB client connection"""
        self.client.close()