import logging
import asyncio
from starlette.websockets import WebSocketState, WebSocketDisconnect

logger = logging.getLogger("app")

class TrafficSimulator:
    def __init__(self):

        self.connections = {}

    async def start_simulation(self, connection_id, websocket):
        logger.info(f"Entering start_simulation for connection {connection_id}")

        self.connections[connection_id] = websocket
        logger.info(f"Simulation started for connection {connection_id}")
        try:
            logger.info(f"Starting simulation loop for connection {connection_id}")
            while True:
                logger.info(f"Simulation loop running for {connection_id}. WebSocket state: {websocket.client_state}")
                # Placeholder for actual traffic simulation logic
                # In a real scenario, this would generate traffic data
                # and send it to the frontend via the websocket.
                try:
                    logger.info(f"Before checking WebSocket state for {connection_id}. Current state: {websocket.client_state}")
                    if websocket.client_state == WebSocketState.CONNECTED:
                        logger.info(f"WebSocket {connection_id} is CONNECTED. Proceeding to send data.")
                        # Generate dummy data that matches the frontend's expected structure
                        current_time = asyncio.get_event_loop().time()
                        logger.info(f"Generating dummy data for {connection_id} at time {current_time}")
                        logger.info(f"Preparing to send data to {connection_id}")
                        dummy_data = {
                            "signals": {"north": "RED", "south": "GREEN", "east": "RED", "west": "GREEN"},
                            "sensorData": {
                                "northQueue": {"count": 5},
                                 "southQueue": {"count": 3},
                                 "eastQueue": {"count": 7},
                                 "westQueue": {"count": 2},
                                "emergencyDetected": False,
                                "congestionLevel": "LOW"
                            },
                            "aiMetrics": {
                                "efficiency": 75, "responseTime": "0.5ms", "accuracy": "90%",
                                "algorithm": "Reinforcement Learning", "recommendation": "ADJUST_SIGNALS"
                            },
                            "timings": {"currentPhase": "EAST_WEST_GREEN", "timeRemaining": 15, "nextPhase": "NORTH_SOUTH_GREEN"}
                        }
                        # await websocket.send_json(dummy_data)
                        # logger.info(f"Dummy data sent to {connection_id}: {dummy_data}")
                    else:
                        logger.info(f"WebSocket {connection_id} not connected (State: {websocket.client_state}), stopping simulation for this connection.")

                        break # Exit the while loop for this connection
                except TypeError as json_error:
                    logger.error(f"JSON serialization error for {connection_id}: {json_error}", exc_info=True)
                except (RuntimeError, WebSocketDisconnect) as e:
                    logging.error(f"WebSocket send error for {connection_id}: {e}", exc_info=True)
                    break
                # await asyncio.sleep(1) # Simulate data every 1 second
        except WebSocketDisconnect:
            logger.info(f"WebSocket connection {connection_id} disconnected during simulation.")

        except Exception as e:
            logger.error(f"Simulation error for {connection_id}: {e}", exc_info=True)

        finally:
            del self.connections[connection_id]
            logger.info(f"Simulation stopped for connection {connection_id}")