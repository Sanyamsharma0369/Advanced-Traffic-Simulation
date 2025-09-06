"""
Edge-Impulse ML model for real-time vehicle density and arrival time prediction.
This module provides integration with Edge Impulse for efficient on-device ML inference.
"""

import numpy as np
import os
import json
import requests
from typing import Dict, List, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EdgeImpulseModel:
    """
    Edge Impulse model for real-time vehicle detection and traffic density prediction.
    This class provides methods to interact with Edge Impulse deployed models.
    """
    
    def __init__(self, model_path: str = None, api_key: str = None, project_id: str = None):
        """
        Initialize the Edge Impulse model.
        
        Args:
            model_path: Path to the local Edge Impulse model (if using local inference)
            api_key: Edge Impulse API key (if using cloud inference)
            project_id: Edge Impulse project ID (if using cloud inference)
        """
        self.model_path = model_path
        self.api_key = api_key
        self.project_id = project_id
        self.model = None
        
        # Check if we're using local or cloud inference
        self.use_local = model_path is not None
        self.use_cloud = api_key is not None and project_id is not None
        
        if not self.use_local and not self.use_cloud:
            logger.warning("Neither local model path nor cloud credentials provided. "
                          "Please provide either model_path or (api_key and project_id).")
        
        # Load local model if available
        if self.use_local:
            self._load_local_model()
    
    def _load_local_model(self):
        """
        Load the local Edge Impulse model.
        """
        try:
            # Import Edge Impulse library dynamically to avoid dependency issues
            # if the library is not installed
            from edge_impulse_linux import EdgeImpulseImpulseRunner
            
            model_path = os.path.expanduser(self.model_path)
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            # Initialize the Edge Impulse runner
            self.model = EdgeImpulseImpulseRunner(model_path)
            
            # Initialize the model
            self.model.init()
            
            logger.info(f"Local Edge Impulse model loaded from {model_path}")
            
        except ImportError:
            logger.error("Failed to import Edge Impulse library. "
                        "Please install it with 'pip install edge_impulse_linux'")
            raise
        except Exception as e:
            logger.error(f"Failed to load local Edge Impulse model: {str(e)}")
            raise
    
    def _cloud_inference(self, data: Dict) -> Dict:
        """
        Perform inference using Edge Impulse cloud API.
        
        Args:
            data: Input data for inference
            
        Returns:
            Inference results
        """
        if not self.use_cloud:
            raise ValueError("Cloud inference not configured. "
                           "Please provide api_key and project_id.")
        
        url = f"https://api.edgeimpulse.com/v1/api/{self.project_id}/predict"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Cloud inference failed: {str(e)}")
            raise
    
    def _local_inference(self, features: List[float]) -> Dict:
        """
        Perform inference using local Edge Impulse model.
        
        Args:
            features: Input features for inference
            
        Returns:
            Inference results
        """
        if not self.use_local:
            raise ValueError("Local inference not configured. Please provide model_path.")
        
        if self.model is None:
            self._load_local_model()
        
        try:
            # Convert features to the format expected by Edge Impulse
            features = np.array(features, dtype=np.float32)
            
            # Run inference
            result = self.model.classify(features)
            
            if result["result"]["classification"]:
                return {
                    "success": True,
                    "predictions": result["result"]["classification"]
                }
            else:
                return {
                    "success": True,
                    "predictions": result["result"]["regression"]
                }
        except Exception as e:
            logger.error(f"Local inference failed: {str(e)}")
            raise
    
    def predict_vehicle_density(self, 
                               sensor_data: Union[List[float], Dict], 
                               use_cloud: bool = None) -> Dict:
        """
        Predict vehicle density using Edge Impulse model.
        
        Args:
            sensor_data: Sensor data for prediction (format depends on inference type)
            use_cloud: Override default inference type
            
        Returns:
            Dictionary with prediction results
        """
        # Determine inference type
        if use_cloud is None:
            use_cloud = self.use_cloud and not self.use_local
        
        try:
            if use_cloud:
                # Format data for cloud inference
                if isinstance(sensor_data, list):
                    data = {"features": sensor_data}
                else:
                    data = sensor_data
                
                return self._cloud_inference(data)
            else:
                # Format data for local inference
                if isinstance(sensor_data, dict):
                    features = sensor_data.get("features", [])
                else:
                    features = sensor_data
                
                return self._local_inference(features)
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def predict_arrival_time(self, 
                            vehicle_density: float, 
                            distance: float, 
                            speed_limit: float) -> float:
        """
        Predict vehicle arrival time based on density, distance, and speed limit.
        
        Args:
            vehicle_density: Current vehicle density (vehicles per km)
            distance: Distance to intersection (meters)
            speed_limit: Speed limit (km/h)
            
        Returns:
            Estimated arrival time in seconds
        """
        # Convert distance to km
        distance_km = distance / 1000.0
        
        # Calculate base travel time assuming free flow at speed limit
        base_time = (distance_km / speed_limit) * 3600  # seconds
        
        # Adjust for traffic density
        # Higher density means slower speeds
        # This is a simple model; more complex models could be used
        density_factor = 1.0 + (vehicle_density / 50.0)  # Assume 50 vehicles/km is heavy traffic
        
        # Calculate adjusted arrival time
        arrival_time = base_time * density_factor
        
        return arrival_time
    
    def process_camera_frame(self, frame, detection_threshold: float = 0.5) -> Dict:
        """
        Process a camera frame to detect vehicles.
        
        Args:
            frame: Camera frame (numpy array or path to image)
            detection_threshold: Confidence threshold for detection
            
        Returns:
            Dictionary with detection results
        """
        try:
            import cv2
            
            # Load image if path is provided
            if isinstance(frame, str):
                frame = cv2.imread(frame)
                if frame is None:
                    raise ValueError(f"Failed to load image from {frame}")
            
            # Preprocess frame for Edge Impulse
            # Resize to expected input size (depends on model)
            # For example, resize to 96x96 for a typical object detection model
            resized_frame = cv2.resize(frame, (96, 96))
            
            # Convert to RGB if needed
            if len(resized_frame.shape) == 3 and resized_frame.shape[2] == 3:
                resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            
            # Flatten and normalize
            features = resized_frame.flatten().astype(np.float32) / 255.0
            
            # Run inference
            result = self.predict_vehicle_density(features.tolist())
            
            if not result["success"]:
                return result
            
            # Process results
            predictions = result["predictions"]
            detections = []
            
            # Format depends on model type (classification vs object detection)
            if "bounding_boxes" in result:
                # Object detection model
                for box in result["bounding_boxes"]:
                    if box["value"] >= detection_threshold:
                        detections.append({
                            "label": box["label"],
                            "confidence": box["value"],
                            "bbox": [box["x"], box["y"], box["width"], box["height"]]
                        })
            else:
                # Classification model
                for label, confidence in predictions.items():
                    if confidence >= detection_threshold:
                        detections.append({
                            "label": label,
                            "confidence": confidence
                        })
            
            return {
                "success": True,
                "detections": detections,
                "vehicle_count": len([d for d in detections if "vehicle" in d["label"].lower()])
            }
            
        except Exception as e:
            logger.error(f"Frame processing failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def calculate_traffic_density(self, vehicle_count: int, road_length: float = 0.1) -> float:
        """
        Calculate traffic density based on vehicle count and road length.
        
        Args:
            vehicle_count: Number of vehicles detected
            road_length: Length of road segment in kilometers
            
        Returns:
            Traffic density (vehicles per kilometer)
        """
        return vehicle_count / road_length