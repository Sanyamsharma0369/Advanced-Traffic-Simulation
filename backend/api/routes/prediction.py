"""
Prediction API Routes
Handles ML-based traffic prediction and optimization
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import requests

from database.connectors.influxdb_connector import InfluxDBConnector
from database.connectors.postgres_connector import PostgresConnector
from database.connectors.redis_connector import RedisConnector

router = APIRouter(
    prefix="/prediction",
    tags=["prediction"],
    responses={404: {"description": "Not found"}},
)

# Initialize database connectors
influxdb = InfluxDBConnector()
postgres = PostgresConnector()
redis = RedisConnector()

class PredictionRequest(BaseModel):
    intersection_id: str
    prediction_window: int = 30  # minutes
    include_historical: bool = False

class OptimizationRequest(BaseModel):
    intersection_id: str
    algorithm: str
    parameters: Optional[Dict[str, Any]] = None

@router.post("/traffic-flow")
async def predict_traffic_flow(request: PredictionRequest):
    """
    Predict traffic flow for a specific intersection
    """
    try:
        # Get current system settings
        settings = redis.get("system:settings")
        if not settings:
            with postgres.get_session() as session:
                from database.models.postgres_models import SystemSettings
                db_settings = session.query(SystemSettings).order_by(SystemSettings.created_at.desc()).first()
                if db_settings:
                    settings = {
                        "ml_model_type": db_settings.ml_model_type,
                        "optimization_algorithm": db_settings.optimization_algorithm
                    }
                else:
                    settings = {"ml_model_type": "edge_impulse", "optimization_algorithm": "afsa"}
        
        # Get historical data for prediction
        start_time = datetime.utcnow() - timedelta(hours=24)
        end_time = datetime.utcnow()
        
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "traffic_volume")
            |> filter(fn: (r) => r.intersection_id == "{request.intersection_id}")
            |> aggregateWindow(every: 5m, fn: sum)
            |> yield(name: "sum")
        '''
        
        historical_data = influxdb.query_data(query)
        
        # In a real system, we would call the ML service here
        # For now, we'll simulate a prediction
        
        # Prepare prediction input
        prediction_input = {
            "intersection_id": request.intersection_id,
            "historical_data": historical_data,
            "prediction_window": request.prediction_window,
            "model_type": settings.get("ml_model_type", "edge_impulse")
        }
        
        # Call ML service (simulated)
        # In a real system, this would be an HTTP request to the ML service
        # ml_service_url = "http://ml-service:5000/predict"
        # response = requests.post(ml_service_url, json=prediction_input)
        # prediction_result = response.json()
        
        # Simulate prediction result
        current_time = datetime.utcnow()
        prediction_result = {
            "intersection_id": request.intersection_id,
            "prediction_time": current_time.isoformat(),
            "model_type": settings.get("ml_model_type", "edge_impulse"),
            "predictions": []
        }
        
        # Generate simulated predictions
        for i in range(request.prediction_window):
            timestamp = current_time + timedelta(minutes=i)
            # Simple simulation based on time of day
            hour = timestamp.hour
            # Traffic is higher during morning and evening rush hours
            if 7 <= hour <= 9 or 16 <= hour <= 18:
                volume = 80 + ((i % 5) * 10)  # Higher volume during rush hours
            else:
                volume = 30 + ((i % 5) * 5)   # Lower volume during off-peak
                
            prediction_result["predictions"].append({
                "timestamp": timestamp.isoformat(),
                "volume": volume,
                "confidence": 0.85 - (i * 0.01)  # Confidence decreases with prediction distance
            })
            
        # Include historical data if requested
        if request.include_historical:
            prediction_result["historical_data"] = historical_data
            
        return prediction_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting traffic flow: {str(e)}")

@router.post("/optimize")
async def optimize_timing(request: OptimizationRequest):
    """
    Optimize signal timing for a specific intersection
    """
    try:
        # Get current intersection data
        with postgres.get_session() as session:
            from database.models.postgres_models import Intersection, Signal, TimingPlan
            intersection = session.query(Intersection).filter(Intersection.id == request.intersection_id).first()
            
            if not intersection:
                raise HTTPException(status_code=404, detail=f"Intersection {request.intersection_id} not found")
                
            signals = session.query(Signal).filter(Signal.intersection_id == request.intersection_id).all()
            current_timing = session.query(TimingPlan).filter(
                TimingPlan.intersection_id == request.intersection_id,
                TimingPlan.is_active == True
            ).first()
            
        # Get recent traffic data
        start_time = datetime.utcnow() - timedelta(hours=6)
        end_time = datetime.utcnow()
        
        query = f'''
        from(bucket: "{influxdb.bucket}")
            |> range(start: {int(start_time.timestamp())}, stop: {int(end_time.timestamp())})
            |> filter(fn: (r) => r._measurement == "traffic_volume" OR r._measurement == "wait_times")
            |> filter(fn: (r) => r.intersection_id == "{request.intersection_id}")
            |> aggregateWindow(every: 15m, fn: mean)
        '''
        
        recent_data = influxdb.query_data(query)
        
        # Prepare optimization input
        optimization_input = {
            "intersection_id": request.intersection_id,
            "intersection_type": intersection.intersection_type,
            "signals": [{"id": s.id, "direction": s.direction, "current_status": s.current_status} for s in signals],
            "current_timing": json.loads(current_timing.timing_data) if current_timing else {},
            "recent_data": recent_data,
            "algorithm": request.algorithm,
            "parameters": request.parameters or {}
        }
        
        # Call ML service for optimization (simulated)
        # In a real system, this would be an HTTP request to the ML service
        # ml_service_url = "http://ml-service:5000/optimize"
        # response = requests.post(ml_service_url, json=optimization_input)
        # optimization_result = response.json()
        
        # Simulate optimization result
        optimization_result = {
            "intersection_id": request.intersection_id,
            "optimization_time": datetime.utcnow().isoformat(),
            "algorithm": request.algorithm,
            "optimized_timing": {
                "cycle_length": 120,
                "phases": [
                    {
                        "id": 1,
                        "signals": ["N-S", "S-N"],
                        "green_time": 45,
                        "yellow_time": 5,
                        "red_time": 70
                    },
                    {
                        "id": 2,
                        "signals": ["E-W", "W-E"],
                        "green_time": 40,
                        "yellow_time": 5,
                        "red_time": 75
                    },
                    {
                        "id": 3,
                        "signals": ["N-E", "S-W"],
                        "green_time": 15,
                        "yellow_time": 3,
                        "red_time": 102
                    }
                ]
            },
            "estimated_improvements": {
                "wait_time_reduction": 18.5,  # percentage
                "throughput_increase": 12.3,  # percentage
                "congestion_reduction": 15.7  # percentage
            }
        }
        
        # Store optimization result in database
        with postgres.get_session() as session:
            from database.models.postgres_models import OptimizationRun
            
            # Create new optimization run record
            new_run = OptimizationRun(
                intersection_id=request.intersection_id,
                algorithm=request.algorithm,
                parameters=json.dumps(request.parameters) if request.parameters else None,
                result_data=json.dumps(optimization_result),
                created_at=datetime.utcnow()
            )
            
            session.add(new_run)
            session.commit()
            
            optimization_result["run_id"] = new_run.id
            
        return optimization_result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing timing: {str(e)}")

@router.get("/models")
async def get_available_models():
    """
    Get available ML models for traffic prediction
    """
    try:
        # In a real system, this would query the ML service
        # For now, we'll return a static list
        
        models = [
            {
                "id": "edge_impulse_v1",
                "name": "Edge Impulse",
                "version": "1.0",
                "type": "edge_impulse",
                "description": "Lightweight ML model optimized for edge devices",
                "accuracy": 0.89,
                "latency": "15ms"
            },
            {
                "id": "mlp_nn_v2",
                "name": "MLP Neural Network",
                "version": "2.0",
                "type": "mlp_nn",
                "description": "Multi-layer perceptron neural network for traffic prediction",
                "accuracy": 0.92,
                "latency": "45ms"
            },
            {
                "id": "lstm_v1",
                "name": "LSTM Time Series",
                "version": "1.0",
                "type": "lstm",
                "description": "Long Short-Term Memory network for time series prediction",
                "accuracy": 0.94,
                "latency": "120ms"
            }
        ]
        
        return {
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving available models: {str(e)}")

@router.get("/algorithms")
async def get_optimization_algorithms():
    """
    Get available optimization algorithms
    """
    try:
        # In a real system, this would query the ML service
        # For now, we'll return a static list
        
        algorithms = [
            {
                "id": "afsa",
                "name": "Artificial Fish Swarm Algorithm",
                "description": "Bio-inspired optimization algorithm based on fish swarm behavior",
                "parameters": [
                    {"name": "population_size", "type": "integer", "default": 50, "description": "Size of the fish population"},
                    {"name": "max_iterations", "type": "integer", "default": 100, "description": "Maximum number of iterations"},
                    {"name": "visual_range", "type": "float", "default": 5.0, "description": "Visual range of each fish"}
                ]
            },
            {
                "id": "genetic",
                "name": "Genetic Algorithm",
                "description": "Evolutionary algorithm for traffic signal optimization",
                "parameters": [
                    {"name": "population_size", "type": "integer", "default": 100, "description": "Size of the population"},
                    {"name": "mutation_rate", "type": "float", "default": 0.1, "description": "Probability of mutation"},
                    {"name": "crossover_rate", "type": "float", "default": 0.8, "description": "Probability of crossover"}
                ]
            },
            {
                "id": "reinforcement",
                "name": "Reinforcement Learning",
                "description": "Q-learning based approach for adaptive signal control",
                "parameters": [
                    {"name": "learning_rate", "type": "float", "default": 0.1, "description": "Learning rate"},
                    {"name": "discount_factor", "type": "float", "default": 0.9, "description": "Discount factor for future rewards"},
                    {"name": "exploration_rate", "type": "float", "default": 0.2, "description": "Exploration rate"}
                ]
            }
        ]
        
        return {
            "algorithms": algorithms,
            "count": len(algorithms)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving optimization algorithms: {str(e)}")

@router.get("/history/{intersection_id}")
async def get_optimization_history(intersection_id: str):
    """
    Get optimization history for a specific intersection
    """
    try:
        with postgres.get_session() as session:
            from database.models.postgres_models import OptimizationRun
            
            runs = session.query(OptimizationRun).filter(
                OptimizationRun.intersection_id == intersection_id
            ).order_by(OptimizationRun.created_at.desc()).limit(10).all()
            
            history = []
            for run in runs:
                result_data = json.loads(run.result_data)
                history.append({
                    "run_id": run.id,
                    "intersection_id": run.intersection_id,
                    "algorithm": run.algorithm,
                    "parameters": json.loads(run.parameters) if run.parameters else None,
                    "created_at": run.created_at.isoformat(),
                    "estimated_improvements": result_data.get("estimated_improvements", {})
                })
                
            return {
                "intersection_id": intersection_id,
                "optimization_history": history,
                "count": len(history)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving optimization history: {str(e)}")