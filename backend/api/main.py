"""
Main FastAPI application for Smart Traffic Light Controller System
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from typing import Dict, Any
from datetime import datetime

import logging
from logging.handlers import RotatingFileHandler

# Import API routes
from .routes import signal_control, analytics, system, prediction
from .utils.traffic_simulator import TrafficSimulator

logger = logging.getLogger("app")



# Create FastAPI app
app = FastAPI(
    title="Smart Traffic Light Controller API",
    description="API for controlling and optimizing traffic signals using ML algorithms",
    version="1.0.0",
)

logger.info("FastAPI application initialized.")


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(signal_control.router)
app.include_router(analytics.router)
app.include_router(system.router)
app.include_router(prediction.router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Smart Traffic Light Controller API",
        "version": "1.0.0",
        "status": "online",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # In a real system, this would check database connections, etc.
    return {
        "status": "healthy",
        "services": {
            "api": "online",
            "database": "online",
            "ml_service": "online",
        }
    }

import uuid
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
import json

active_connections: dict[str, WebSocket] = {}
traffic_simulator = TrafficSimulator()

@app.websocket("/traffic-stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Attempting WebSocket connection.")
    logger.info("WebSocket connection accepted.")
    connection_id = str(uuid.uuid4())
    active_connections[connection_id] = websocket

    try:
        # Initial data send (optional, based on frontend needs)
        # await websocket.send_json({"message": "Connected to traffic stream"})

        logger.info(f"Calling start_simulation for connection {connection_id}")
        await traffic_simulator.start_simulation(connection_id, websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection {connection_id} disconnected.")
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)