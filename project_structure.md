# Project Structure

```
/
├── frontend/                      # React + TypeScript frontend application
│   ├── public/                    # Static assets
│   └── src/                       # Source code
│       ├── components/            # React components
│       ├── pages/                 # Page components
│       ├── services/              # API services
│       ├── utils/                 # Utility functions
│       └── App.tsx                # Main application component
│
├── backend/                       # Python FastAPI backend services
│   ├── api/                       # API endpoints
│   │   ├── routes/                # API route definitions
│   │   └── models/                # API data models
│   ├── core/                      # Core application code
│   │   ├── config/                # Configuration
│   │   └── security/              # Security utilities
│   ├── ml/                        # Machine learning models
│   │   ├── prediction/            # Traffic prediction models
│   │   ├── optimization/          # Signal optimization algorithms
│   │   └── training/              # Model training scripts
│   ├── services/                  # Microservices
│   │   ├── traffic_prediction/    # Traffic prediction service
│   │   ├── signal_control/        # Signal control service
│   │   ├── data_processing/       # Data processing service
│   │   ├── emergency_management/  # Emergency management service
│   │   └── iot_management/        # IoT device management service
│   └── tests/                     # Backend tests
│
├── embedded/                      # C/C++ code for embedded systems
│   ├── controllers/               # Traffic light controllers
│   ├── sensors/                   # Sensor interfaces
│   └── communication/             # Communication protocols
│
├── iot/                           # IoT device code
│   ├── raspberry_pi/              # Raspberry Pi code
│   ├── arduino/                   # Arduino-compatible code
│   └── protocols/                 # Communication protocols
│
├── database/                      # Database scripts and migrations
│   ├── postgresql/                # PostgreSQL schemas and migrations
│   ├── influxdb/                  # InfluxDB configurations
│   └── redis/                     # Redis configurations
│
├── deployment/                    # Deployment configurations
│   ├── docker/                    # Docker configurations
│   │   ├── frontend/              # Frontend Docker configuration
│   │   ├── backend/               # Backend Docker configuration
│   │   └── docker-compose.yml     # Docker Compose configuration
│   └── kubernetes/                # Kubernetes configurations
│       ├── frontend/              # Frontend K8s manifests
│       ├── backend/               # Backend K8s manifests
│       └── database/              # Database K8s manifests
│
├── docs/                          # Documentation
│   ├── api.md                     # API documentation
│   ├── architecture.md            # Architecture documentation
│   ├── deployment.md              # Deployment documentation
│   └── developer.md               # Developer documentation
│
└── tests/                         # Integration and performance tests
    ├── integration/               # Integration tests
    └── performance/               # Performance benchmarking scripts
```