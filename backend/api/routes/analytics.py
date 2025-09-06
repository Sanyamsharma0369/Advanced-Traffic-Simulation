"""
Analytics API Routes
Handles traffic data analysis and reporting
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from database.connectors.influxdb_connector import InfluxDBConnector
from database.connectors.postgres_connector import PostgresConnector

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

# Initialize database connectors
influxdb = InfluxDBConnector()
postgres = PostgresConnector()

@router.get("/traffic-volume/{intersection_id}")
async def get_traffic_volume(
    intersection_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: str = "1h"
):
    """
    Get traffic volume data for a specific intersection
    """
    if not start_time:
        start_time = datetime.utcnow() - timedelta(hours=24)
    
    if not end_time:
        end_time = datetime.utcnow()
        
    try:
        # Query InfluxDB for traffic volume data
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "traffic_volume")
            |> filter(fn: (r) => r.intersection_id == "{intersection_id}")
            |> aggregateWindow(every: {interval}, fn: sum)
        '''
        
        results = influxdb.query_data(query)
        
        if not results:
            return {
                "intersection_id": intersection_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "interval": interval,
                "data": []
            }
            
        return {
            "intersection_id": intersection_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "interval": interval,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving traffic volume: {str(e)}")

@router.get("/wait-times/{intersection_id}")
async def get_wait_times(
    intersection_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    interval: str = "1h"
):
    """
    Get average wait times for a specific intersection
    """
    if not start_time:
        start_time = datetime.utcnow() - timedelta(hours=24)
    
    if not end_time:
        end_time = datetime.utcnow()
        
    try:
        # Query InfluxDB for wait time data
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "wait_times")
            |> filter(fn: (r) => r.intersection_id == "{intersection_id}")
            |> aggregateWindow(every: {interval}, fn: mean)
        '''
        
        results = influxdb.query_data(query)
        
        return {
            "intersection_id": intersection_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "interval": interval,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving wait times: {str(e)}")

@router.get("/performance/{intersection_id}")
async def get_performance_metrics(
    intersection_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """
    Get performance metrics for a specific intersection
    """
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=7)
    
    if not end_time:
        end_time = datetime.utcnow()
        
    try:
        # Query InfluxDB for performance metrics
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "performance_metrics")
            |> filter(fn: (r) => r.intersection_id == "{intersection_id}")
        '''
        
        results = influxdb.query_data(query)
        
        # Calculate improvement metrics
        before_optimization = next((r for r in results if r.get("optimization_status") == "before"), {})
        after_optimization = next((r for r in results if r.get("optimization_status") == "after"), {})
        
        improvements = {}
        if before_optimization and after_optimization:
            for key in ["avg_wait_time", "throughput", "congestion_level"]:
                if key in before_optimization and key in after_optimization:
                    before_val = float(before_optimization.get(key, 0))
                    after_val = float(after_optimization.get(key, 0))
                    
                    if before_val > 0:
                        improvement = ((after_val - before_val) / before_val) * 100
                        improvements[key] = improvement
        
        return {
            "intersection_id": intersection_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "metrics": results,
            "improvements": improvements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")

@router.get("/vehicle-types/{intersection_id}")
async def get_vehicle_type_distribution(
    intersection_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """
    Get vehicle type distribution for a specific intersection
    """
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=1)
    
    if not end_time:
        end_time = datetime.utcnow()
        
    try:
        # Query InfluxDB for vehicle type data
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "vehicle_types")
            |> filter(fn: (r) => r.intersection_id == "{intersection_id}")
            |> group(columns: ["vehicle_type"])
            |> sum()
        '''
        
        results = influxdb.query_data(query)
        
        # Process results into a distribution
        vehicle_counts = {}
        total_count = 0
        
        for record in results:
            vehicle_type = record.get("vehicle_type", "unknown")
            count = float(record.get("_value", 0))
            
            vehicle_counts[vehicle_type] = count
            total_count += count
            
        # Calculate percentages
        distribution = {}
        if total_count > 0:
            for vehicle_type, count in vehicle_counts.items():
                distribution[vehicle_type] = (count / total_count) * 100
                
        return {
            "intersection_id": intersection_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_vehicles": total_count,
            "distribution": distribution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving vehicle type distribution: {str(e)}")

@router.get("/system-overview")
async def get_system_overview():
    """
    Get system-wide overview statistics
    """
    try:
        # Get intersection count from PostgreSQL
        with postgres.get_session() as session:
            from database.models.postgres_models import Intersection
            intersection_count = session.query(Intersection).filter(Intersection.is_active == True).count()
            
        # Get recent performance metrics from InfluxDB
        start_time = datetime.utcnow() - timedelta(hours=24)
        end_time = datetime.utcnow()
        
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "system_metrics")
            |> last()
        '''
        
        results = influxdb.query_data(query)
        
        # Extract metrics
        metrics = {}
        for record in results:
            field = record.get("_field", "")
            value = record.get("_value", 0)
            metrics[field] = value
            
        return {
            "active_intersections": intersection_count,
            "last_24h_metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system overview: {str(e)}")

@router.get("/reports/daily")
async def generate_daily_report(date: Optional[datetime] = None):
    """
    Generate a daily traffic report
    """
    if not date:
        date = datetime.utcnow() - timedelta(days=1)
        
    start_time = datetime(date.year, date.month, date.day, 0, 0, 0)
    end_time = start_time + timedelta(days=1)
    
    try:
        # Query InfluxDB for daily metrics
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "daily_metrics")
        '''
        
        results = influxdb.query_data(query)
        
        return {
            "report_type": "daily",
            "date": start_time.date().isoformat(),
            "metrics": results,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily report: {str(e)}")