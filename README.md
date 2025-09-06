# Real-Time Smart Traffic Light Controller

A comprehensive system for intelligent traffic management using machine learning and real-time data processing.

## System Architecture

This project implements a three-tier architecture:

1. **Field Level (Embedded Systems)**
   - Traffic light controllers
   - Vehicle sensors and cameras
   - Pedestrian detection systems
   - Emergency vehicle detectors

2. **Edge Computing Layer**
   - Real-time traffic analysis
   - Local decision making
   - Backup autonomous operation
   - V2X communication handling

3. **Central Control System**
   - City-wide traffic coordination
   - Predictive analytics
   - System monitoring and maintenance
   - Data storage and historical analysis

## Core Features

- Multi-objective optimization algorithm for traffic signal timing
- Edge-Impulse ML model for real-time vehicle density prediction
- Artificial Fish Swarm Algorithm (AFSA) for signal timing optimization
- Multilayer Perceptron Neural Network (MLP-NN) with 0.93 R-squared accuracy
- Emergency vehicle detection with priority preemption
- Dynamic green wave coordination for consecutive intersections
- Autonomous operation during network failures
- Weather and event-based traffic prediction

## Technology Stack

- **Frontend:** React + TypeScript, MapBox GL JS, Socket.io
- **Backend:** Python FastAPI, C++ for real-time control
- **ML/AI:** TensorFlow, scikit-learn, OpenCV
- **Database:** PostgreSQL, InfluxDB, Redis
- **IoT:** MQTT, Raspberry Pi, Arduino-compatible sensors
- **Cloud:** Kubernetes, Docker, CI/CD pipelines

## Getting Started

See the [Installation Guide](docs/installation.md) for setup instructions.

## Documentation

- [API Documentation](docs/api.md)
- [Architecture Overview](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Developer Guide](docs/developer.md)