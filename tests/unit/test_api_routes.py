"""
Unit tests for API routes
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.api.main import app
from database.models.postgres_models import Intersection, Signal, TimingPlan, SystemSettings


class TestSignalControlRoutes(unittest.TestCase):
    """Test cases for signal control routes"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        
    @patch('backend.api.routes.signal_control.postgres')
    @patch('backend.api.routes.signal_control.redis')
    def test_get_intersection_status(self, mock_redis, mock_postgres):
        """Test get_intersection_status endpoint"""
        # Mock PostgreSQL session and query results
        mock_session = MagicMock()
        mock_postgres.get_session.return_value.__enter__.return_value = mock_session
        
        mock_intersection = MagicMock()
        mock_intersection.id = "test-intersection-1"
        mock_intersection.name = "Test Intersection"
        mock_intersection.location = "Test Location"
        mock_intersection.intersection_type = "four_way"
        mock_intersection.is_active = True
        
        mock_signals = [
            MagicMock(id="signal-1", direction="N-S", current_status="GREEN"),
            MagicMock(id="signal-2", direction="E-W", current_status="RED")
        ]
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_intersection
        mock_session.query.return_value.filter.return_value.all.return_value = mock_signals
        
        # Mock Redis cache
        mock_redis.get.return_value = None
        
        # Make request
        response = self.client.get("/signal-control/intersections/test-intersection-1")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "test-intersection-1")
        self.assertEqual(data["name"], "Test Intersection")
        self.assertEqual(len(data["signals"]), 2)
        
    @patch('backend.api.routes.signal_control.postgres')
    @patch('backend.api.routes.signal_control.redis')
    def test_update_signal_status(self, mock_redis, mock_postgres):
        """Test update_signal_status endpoint"""
        # Mock PostgreSQL session and query results
        mock_session = MagicMock()
        mock_postgres.get_session.return_value.__enter__.return_value = mock_session
        
        mock_signal = MagicMock()
        mock_signal.id = "signal-1"
        mock_signal.direction = "N-S"
        mock_signal.current_status = "RED"
        mock_signal.intersection_id = "test-intersection-1"
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_signal
        
        # Make request
        response = self.client.put(
            "/signal-control/signals/signal-1",
            json={"status": "GREEN"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "signal-1")
        self.assertEqual(data["status"], "GREEN")
        
        # Check that signal was updated
        self.assertEqual(mock_signal.current_status, "GREEN")
        mock_session.commit.assert_called_once()
        
        # Check that Redis was updated
        mock_redis.publish.assert_called_once()
        
    @patch('backend.api.routes.signal_control.postgres')
    def test_update_timing_plan(self, mock_postgres):
        """Test update_timing_plan endpoint"""
        # Mock PostgreSQL session and query results
        mock_session = MagicMock()
        mock_postgres.get_session.return_value.__enter__.return_value = mock_session
        
        mock_intersection = MagicMock()
        mock_intersection.id = "test-intersection-1"
        
        mock_timing_plan = MagicMock()
        mock_timing_plan.id = "timing-1"
        mock_timing_plan.intersection_id = "test-intersection-1"
        mock_timing_plan.is_active = True
        
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_intersection,  # First query for intersection
            mock_timing_plan    # Second query for timing plan
        ]
        
        # Make request
        new_timing_data = {
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
                }
            ]
        }
        
        response = self.client.put(
            "/signal-control/timing-plans/test-intersection-1",
            json={"timing_data": new_timing_data}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intersection_id"], "test-intersection-1")
        
        # Check that timing plan was updated
        mock_session.commit.assert_called_once()


class TestAnalyticsRoutes(unittest.TestCase):
    """Test cases for analytics routes"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        
    @patch('backend.api.routes.analytics.influxdb')
    def test_get_traffic_volume(self, mock_influxdb):
        """Test get_traffic_volume endpoint"""
        # Mock InfluxDB query results
        mock_influxdb.query_data.return_value = [
            {"_time": "2023-01-01T12:00:00Z", "_value": 150},
            {"_time": "2023-01-01T13:00:00Z", "_value": 200}
        ]
        
        # Make request
        response = self.client.get("/analytics/traffic-volume/test-intersection-1")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intersection_id"], "test-intersection-1")
        self.assertEqual(len(data["data"]), 2)
        
    @patch('backend.api.routes.analytics.influxdb')
    def test_get_wait_times(self, mock_influxdb):
        """Test get_wait_times endpoint"""
        # Mock InfluxDB query results
        mock_influxdb.query_data.return_value = [
            {"_time": "2023-01-01T12:00:00Z", "_value": 25.5},
            {"_time": "2023-01-01T13:00:00Z", "_value": 18.2}
        ]
        
        # Make request
        response = self.client.get("/analytics/wait-times/test-intersection-1")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intersection_id"], "test-intersection-1")
        self.assertEqual(len(data["data"]), 2)
        
    @patch('backend.api.routes.analytics.influxdb')
    def test_get_vehicle_type_distribution(self, mock_influxdb):
        """Test get_vehicle_type_distribution endpoint"""
        # Mock InfluxDB query results
        mock_influxdb.query_data.return_value = [
            {"vehicle_type": "car", "_value": 150},
            {"vehicle_type": "truck", "_value": 30},
            {"vehicle_type": "bus", "_value": 10},
            {"vehicle_type": "motorcycle", "_value": 10}
        ]
        
        # Make request
        response = self.client.get("/analytics/vehicle-types/test-intersection-1")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intersection_id"], "test-intersection-1")
        self.assertEqual(data["total_vehicles"], 200)
        self.assertEqual(len(data["distribution"]), 4)


class TestSystemRoutes(unittest.TestCase):
    """Test cases for system routes"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        
    @patch('backend.api.routes.system.postgres')
    @patch('backend.api.routes.system.redis')
    def test_get_system_settings(self, mock_redis, mock_postgres):
        """Test get_system_settings endpoint"""
        # Mock Redis cache
        mock_redis.get.return_value = None
        
        # Mock PostgreSQL session and query results
        mock_session = MagicMock()
        mock_postgres.get_session.return_value.__enter__.return_value = mock_session
        
        mock_settings = MagicMock()
        mock_settings.id = "settings-1"
        mock_settings.ml_model_type = "edge_impulse"
        mock_settings.optimization_algorithm = "afsa"
        mock_settings.emergency_vehicle_priority = True
        mock_settings.green_wave_coordination = True
        mock_settings.data_retention_days = 30
        mock_settings.api_endpoint = "http://api.example.com"
        mock_settings.notification_email = "admin@example.com"
        mock_settings.created_at = datetime.utcnow()
        mock_settings.updated_at = None
        
        mock_session.query.return_value.order_by.return_value.first.return_value = mock_settings
        
        # Make request
        response = self.client.get("/system/settings")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ml_model_type"], "edge_impulse")
        self.assertEqual(data["optimization_algorithm"], "afsa")
        self.assertTrue(data["emergency_vehicle_priority"])
        
    @patch('backend.api.routes.system.postgres')
    @patch('backend.api.routes.system.redis')
    def test_update_system_settings(self, mock_redis, mock_postgres):
        """Test update_system_settings endpoint"""
        # Mock PostgreSQL session
        mock_session = MagicMock()
        mock_postgres.get_session.return_value.__enter__.return_value = mock_session
        
        # Make request
        new_settings = {
            "ml_model_type": "mlp_nn",
            "optimization_algorithm": "genetic",
            "emergency_vehicle_priority": True,
            "green_wave_coordination": True,
            "data_retention_days": 60,
            "api_endpoint": "http://new-api.example.com",
            "notification_email": "newemail@example.com"
        }
        
        response = self.client.post("/system/settings", json=new_settings)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["settings"]["ml_model_type"], "mlp_nn")
        
        # Check that settings were added to database
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Check that Redis was updated
        mock_redis.set.assert_called_once()
        mock_redis.publish.assert_called_once()


class TestPredictionRoutes(unittest.TestCase):
    """Test cases for prediction routes"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        
    @patch('backend.api.routes.prediction.redis')
    @patch('backend.api.routes.prediction.influxdb')
    def test_predict_traffic_flow(self, mock_influxdb, mock_redis):
        """Test predict_traffic_flow endpoint"""
        # Mock Redis cache
        mock_redis.get.return_value = {"ml_model_type": "edge_impulse"}
        
        # Mock InfluxDB query results
        mock_influxdb.query_data.return_value = [
            {"_time": "2023-01-01T12:00:00Z", "_value": 150},
            {"_time": "2023-01-01T13:00:00Z", "_value": 200}
        ]
        
        # Make request
        response = self.client.post(
            "/prediction/traffic-flow",
            json={"intersection_id": "test-intersection-1", "prediction_window": 30}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intersection_id"], "test-intersection-1")
        self.assertEqual(data["model_type"], "edge_impulse")
        self.assertEqual(len(data["predictions"]), 30)
        
    @patch('backend.api.routes.prediction.postgres')
    @patch('backend.api.routes.prediction.influxdb')
    def test_optimize_timing(self, mock_influxdb, mock_postgres):
        """Test optimize_timing endpoint"""
        # Mock PostgreSQL session and query results
        mock_session = MagicMock()
        mock_postgres.get_session.return_value.__enter__.return_value = mock_session
        
        mock_intersection = MagicMock()
        mock_intersection.id = "test-intersection-1"
        mock_intersection.intersection_type = "four_way"
        
        mock_signals = [
            MagicMock(id="signal-1", direction="N-S", current_status="GREEN"),
            MagicMock(id="signal-2", direction="E-W", current_status="RED")
        ]
        
        mock_timing_plan = MagicMock()
        mock_timing_plan.timing_data = '{"cycle_length": 120}'
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_intersection
        mock_session.query.return_value.filter.return_value.all.return_value = mock_signals
        
        # Mock InfluxDB query results
        mock_influxdb.query_data.return_value = [
            {"_time": "2023-01-01T12:00:00Z", "_value": 150},
            {"_time": "2023-01-01T13:00:00Z", "_value": 200}
        ]
        
        # Make request
        response = self.client.post(
            "/prediction/optimize",
            json={"intersection_id": "test-intersection-1", "algorithm": "afsa"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intersection_id"], "test-intersection-1")
        self.assertEqual(data["algorithm"], "afsa")
        self.assertIn("optimized_timing", data)
        self.assertIn("estimated_improvements", data)


if __name__ == '__main__':
    unittest.main()