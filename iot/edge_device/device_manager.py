import json
import time
import logging
import threading
import requests
from typing import Dict, List, Any, Optional
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EdgeDeviceManager")

class EdgeDeviceManager:
    """
    Manages communication between edge devices (cameras, sensors) and the central system.
    Handles MQTT communication, device registration, and data transmission.
    """
    
    def __init__(
        self, 
        device_id: str,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        api_endpoint: str = "http://localhost:8000",
        update_interval: int = 5
    ):
        self.device_id = device_id
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.api_endpoint = api_endpoint
        self.update_interval = update_interval
        
        # Device status
        self.status = "initializing"
        self.connected = False
        self.last_heartbeat = time.time()
        
        # Sensor data cache
        self.sensor_data = {}
        
        # MQTT client setup
        self.mqtt_client = mqtt.Client(client_id=f"edge-device-{device_id}")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message
        
        # Topics
        self.command_topic = f"traffic/devices/{device_id}/commands"
        self.status_topic = f"traffic/devices/{device_id}/status"
        self.data_topic = f"traffic/devices/{device_id}/data"
        
        # Background threads
        self.heartbeat_thread = None
        self.data_thread = None
        self.running = False
    
    def start(self):
        """Start the device manager and connect to MQTT broker"""
        try:
            logger.info(f"Starting edge device manager for device {self.device_id}")
            self.running = True
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Start background threads
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            self.data_thread = threading.Thread(target=self._data_transmission_loop)
            self.data_thread.daemon = True
            self.data_thread.start()
            
            # Register device with central system
            self._register_device()
            
            self.status = "running"
            logger.info(f"Edge device {self.device_id} started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start edge device manager: {str(e)}")
            self.status = "error"
            return False
    
    def stop(self):
        """Stop the device manager and disconnect from MQTT broker"""
        logger.info(f"Stopping edge device {self.device_id}")
        self.running = False
        self.status = "stopping"
        
        # Publish offline status
        self._publish_status("offline")
        
        # Stop MQTT client
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        
        # Wait for threads to finish
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2.0)
        if self.data_thread:
            self.data_thread.join(timeout=2.0)
        
        self.status = "stopped"
        logger.info(f"Edge device {self.device_id} stopped")
    
    def update_sensor_data(self, sensor_type: str, data: Any):
        """Update sensor data in the local cache"""
        self.sensor_data[sensor_type] = {
            "value": data,
            "timestamp": time.time()
        }
    
    def _register_device(self):
        """Register this device with the central system"""
        try:
            device_info = {
                "device_id": self.device_id,
                "device_type": "traffic_controller",
                "capabilities": ["camera", "traffic_light_control", "vehicle_detection"],
                "location": {
                    "latitude": 0.0,  # To be updated with actual GPS coordinates
                    "longitude": 0.0
                }
            }
            
            # Try to register via API
            try:
                response = requests.post(
                    f"{self.api_endpoint}/api/devices/register",
                    json=device_info,
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info(f"Device {self.device_id} registered successfully via API")
                    return
            except requests.RequestException as e:
                logger.warning(f"API registration failed, falling back to MQTT: {str(e)}")
            
            # Fall back to MQTT registration
            self.mqtt_client.publish(
                "traffic/devices/registration",
                json.dumps(device_info),
                qos=1
            )
            logger.info(f"Device {self.device_id} registration sent via MQTT")
            
        except Exception as e:
            logger.error(f"Failed to register device: {str(e)}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            self.connected = True
            
            # Subscribe to command topic
            client.subscribe(self.command_topic, qos=1)
            logger.info(f"Subscribed to {self.command_topic}")
            
            # Publish online status
            self._publish_status("online")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        logger.warning(f"Disconnected from MQTT broker with code: {rc}")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on {msg.topic}: {payload}")
            
            if msg.topic == self.command_topic:
                self._handle_command(payload)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def _handle_command(self, command: Dict):
        """Handle command received from central system"""
        if "action" not in command:
            logger.warning("Received command without action field")
            return
        
        action = command["action"]
        logger.info(f"Handling command: {action}")
        
        if action == "restart":
            # Simulate device restart
            self.stop()
            time.sleep(2)
            self.start()
        
        elif action == "update_config":
            if "config" in command:
                logger.info(f"Updating configuration: {command['config']}")
                # Apply new configuration
                # ...
        
        elif action == "set_traffic_light":
            if "state" in command:
                logger.info(f"Setting traffic light state to: {command['state']}")
                # Update traffic light state
                # ...
        
        else:
            logger.warning(f"Unknown command action: {action}")
    
    def _publish_status(self, status: str):
        """Publish device status to MQTT"""
        if not self.connected:
            logger.warning("Cannot publish status: not connected to MQTT broker")
            return
        
        status_data = {
            "device_id": self.device_id,
            "status": status,
            "timestamp": time.time(),
            "uptime": time.time() - self.last_heartbeat if status == "online" else 0
        }
        
        self.mqtt_client.publish(
            self.status_topic,
            json.dumps(status_data),
            qos=1,
            retain=True
        )
        logger.debug(f"Published status: {status}")
    
    def _publish_sensor_data(self):
        """Publish sensor data to MQTT"""
        if not self.connected or not self.sensor_data:
            return
        
        data_payload = {
            "device_id": self.device_id,
            "timestamp": time.time(),
            "sensors": self.sensor_data
        }
        
        self.mqtt_client.publish(
            self.data_topic,
            json.dumps(data_payload),
            qos=0
        )
        logger.debug(f"Published sensor data: {len(self.sensor_data)} readings")
    
    def _heartbeat_loop(self):
        """Background thread for sending periodic heartbeats"""
        while self.running:
            if self.connected:
                self._publish_status("online")
                self.last_heartbeat = time.time()
            time.sleep(60)  # Send heartbeat every minute
    
    def _data_transmission_loop(self):
        """Background thread for sending periodic sensor data"""
        while self.running:
            if self.connected:
                self._publish_sensor_data()
            time.sleep(self.update_interval)


if __name__ == "__main__":
    # Example usage
    device_manager = EdgeDeviceManager(
        device_id="intersection-001",
        mqtt_broker="localhost",
        mqtt_port=1883,
        api_endpoint="http://localhost:8000"
    )
    
    try:
        device_manager.start()
        
        # Simulate sensor data updates
        while True:
            # Update with random traffic data
            import random
            device_manager.update_sensor_data("vehicle_count", random.randint(0, 30))
            device_manager.update_sensor_data("queue_length", random.randint(0, 15))
            time.sleep(5)
    
    except KeyboardInterrupt:
        device_manager.stop()