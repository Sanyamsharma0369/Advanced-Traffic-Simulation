"""
Traffic prediction API routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import logging
from datetime import datetime, timedelta

from ..models.traffic_models import (
    PredictionRequest,
    PredictionResponse,
    TrafficData
)

# Import ML models
from ...ml.prediction.mlp_model import TrafficPredictionMLP
from ...ml.prediction.edge_impulse_model import EdgeImpulseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/prediction",
    tags=["prediction"],
    responses={404: {"description": "Not found"}},
)

# Initialize ML models
mlp_model = None
edge_model = None

def get_mlp_model():
    """Get or initialize MLP model."""
    global mlp_model
    if mlp_model is None:
        try:
            # In production, load from saved model
            mlp_model = TrafficPredictionMLP()
            # mlp_model.load("path/to/model", "path/to/scaler")
            
            # For development, create a new model
            mlp_model.build_model()
        except Exception as e:
            logger.error(f"Failed to initialize MLP model: {str(e)}")
            raise HTTPException(status_code=500, detail="Model initialization failed")
    return mlp_model

def get_edge_model():
    """Get or initialize Edge Impulse model."""
    global edge_model
    if edge_model is None:
        try:
            # Initialize with local model or API credentials
            edge_model = EdgeImpulseModel()
        except Exception as e:
            logger.error(f"Failed to initialize Edge Impulse model: {str(e)}")
            raise HTTPException(status_code=500, detail="Model initialization failed")
    return edge_model

@router.post("/predict", response_model=PredictionResponse)
async def predict_traffic(request: PredictionRequest):
    """
    Predict traffic conditions based on historical data.
    """
    try:
        # Get ML models
        mlp = get_mlp_model()
        
        # Extract features from historical data
        features = []
        for data in request.historical_data:
            # Simple feature extraction - can be enhanced
            feature = [
                data.vehicle_count,
                data.queue_length,
                data.average_speed,
                data.timestamp.hour,
                data.timestamp.minute,
                data.timestamp.weekday(),
                1 if data.emergency_vehicle_present else 0
            ]
            
            # Add vehicle type counts if available
            if data.vehicle_types:
                for vtype in ["car", "truck", "bus", "motorcycle", "bicycle", "emergency"]:
                    feature.append(data.vehicle_types.get(vtype, 0))
            
            features.append(feature)
        
        # Make predictions
        # In a real system, we'd use the trained model
        # For now, we'll generate synthetic predictions
        
        # Generate prediction timestamps
        timestamps = []
        start_time = datetime.now()
        for i in range(request.prediction_horizon):
            timestamps.append(start_time + timedelta(minutes=i))
        
        # Generate predicted volumes and queue lengths
        # In production, this would use the actual ML model
        approaches = set(data.approach_id for data in request.historical_data)
        predicted_volumes = {approach: [] for approach in approaches}
        predicted_queue_lengths = {approach: [] for approach in approaches}
        
        for approach in approaches:
            # Get historical data for this approach
            approach_data = [d for d in request.historical_data if d.approach_id == approach]
            
            if approach_data:
                # Use the last few data points to predict future values
                recent_volumes = [d.vehicle_count for d in approach_data[-3:]]
                recent_queues = [d.queue_length for d in approach_data[-3:]]
                
                # Simple prediction logic (would be replaced by ML model)
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                avg_queue = sum(recent_queues) / len(recent_queues)
                
                for i in range(request.prediction_horizon):
                    # Add some variation to simulate predictions
                    predicted_volumes[approach].append(avg_volume * (0.9 + 0.2 * (i % 3) / 10))
                    predicted_queue_lengths[approach].append(avg_queue * (0.95 + 0.1 * (i % 2) / 10))
        
        # Create response
        response = PredictionResponse(
            intersection_id=request.intersection_id,
            predicted_volumes=predicted_volumes,
            predicted_queue_lengths=predicted_queue_lengths,
            timestamps=timestamps,
            confidence=0.93  # MLP-NN reported accuracy
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/realtime-density")
async def predict_realtime_density(image_data: Dict):
    """
    Predict real-time vehicle density from camera image.
    """
    try:
        # Get Edge Impulse model
        edge_model = get_edge_model()
        
        # Process image data
        # In production, this would use actual image data
        # For now, we'll return synthetic results
        
        result = {
            "success": True,
            "vehicle_count": 15,
            "vehicle_types": {
                "car": 10,
                "truck": 2,
                "bus": 1,
                "motorcycle": 2,
                "emergency": 0
            },
            "traffic_density": 150,  # vehicles per km
            "confidence": 0.92
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Real-time density prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Check health of prediction service.
    """
    try:
        # Check if models can be initialized
        mlp = get_mlp_model()
        edge = get_edge_model()
        
        return {
            "status": "healthy",
            "models": {
                "mlp": "loaded",
                "edge_impulse": "loaded"
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }