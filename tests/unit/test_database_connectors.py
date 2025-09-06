"""
Unit tests for database connectors
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connectors.postgres_connector import PostgresConnector
from database.connectors.influxdb_connector import InfluxDBConnector
from database.connectors.redis_connector import RedisConnector


class TestPostgresConnector(unittest.TestCase):
    """Test cases for PostgresConnector"""
    
    @patch('database.connectors.postgres_connector.create_engine')
    @patch('database.connectors.postgres_connector.sessionmaker')
    def setUp(self, mock_sessionmaker, mock_create_engine):
        """Set up test environment"""
        self.mock_engine = MagicMock()
        self.mock_session = MagicMock()
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session
        
        self.connector = PostgresConnector()
    
    def test_get_session(self):
        """Test get_session method"""
        self.connector.get_session()
        self.mock_session.assert_called_once()
    
    @patch('database.connectors.postgres_connector.Base')
    def test_create_tables(self, mock_base):
        """Test create_tables method"""
        self.connector.create_tables()
        mock_base.metadata.create_all.assert_called_once_with(self.mock_engine)
    
    def test_add_item(self):
        """Test add_item method"""
        mock_session = MagicMock()
        self.mock_session.return_value.__enter__.return_value = mock_session
        
        test_item = MagicMock()
        self.connector.add_item(test_item)
        
        mock_session.add.assert_called_once_with(test_item)
        mock_session.commit.assert_called_once()
    
    def test_get_item(self):
        """Test get_item method"""
        mock_session = MagicMock()
        self.mock_session.return_value.__enter__.return_value = mock_session
        
        mock_model = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = "test_result"
        
        result = self.connector.get_item(mock_model, id="test_id")
        
        mock_session.query.assert_called_once_with(mock_model)
        self.assertEqual(result, "test_result")
    
    def test_update_item(self):
        """Test update_item method"""
        mock_session = MagicMock()
        self.mock_session.return_value.__enter__.return_value = mock_session
        
        mock_model = MagicMock()
        mock_query = MagicMock()
        mock_item = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_item
        
        update_data = {"name": "new_name", "value": 123}
        result = self.connector.update_item(mock_model, update_data, id="test_id")
        
        mock_session.query.assert_called_once_with(mock_model)
        self.assertEqual(mock_item.name, "new_name")
        self.assertEqual(mock_item.value, 123)
        mock_session.commit.assert_called_once()
        self.assertEqual(result, mock_item)


class TestInfluxDBConnector(unittest.TestCase):
    """Test cases for InfluxDBConnector"""
    
    @patch('database.connectors.influxdb_connector.InfluxDBClient')
    def setUp(self, mock_influxdb_client):
        """Set up test environment"""
        self.mock_client = MagicMock()
        mock_influxdb_client.return_value = self.mock_client
        
        self.connector = InfluxDBConnector()
    
    def test_write_point(self):
        """Test write_point method"""
        self.mock_client.write_api.return_value = MagicMock()
        
        self.connector.write_point(
            measurement="test_measurement",
            tags={"tag1": "value1"},
            fields={"field1": 123},
            timestamp=datetime.utcnow()
        )
        
        self.mock_client.write_api.assert_called_once()
        self.mock_client.write_api.return_value.write.assert_called_once()
    
    def test_write_batch(self):
        """Test write_batch method"""
        self.mock_client.write_api.return_value = MagicMock()
        
        points = [
            {
                "measurement": "test_measurement",
                "tags": {"tag1": "value1"},
                "fields": {"field1": 123},
                "timestamp": datetime.utcnow()
            },
            {
                "measurement": "test_measurement",
                "tags": {"tag2": "value2"},
                "fields": {"field2": 456},
                "timestamp": datetime.utcnow()
            }
        ]
        
        self.connector.write_batch(points)
        
        self.mock_client.write_api.assert_called_once()
        self.mock_client.write_api.return_value.write.assert_called_once()
    
    def test_query_data(self):
        """Test query_data method"""
        mock_query_api = MagicMock()
        self.mock_client.query_api.return_value = mock_query_api
        mock_query_api.query.return_value = ["test_result"]
        
        result = self.connector.query_data("test_query")
        
        self.mock_client.query_api.assert_called_once()
        mock_query_api.query.assert_called_once()
        self.assertEqual(result, ["test_result"])


class TestRedisConnector(unittest.TestCase):
    """Test cases for RedisConnector"""
    
    @patch('database.connectors.redis_connector.redis.Redis')
    def setUp(self, mock_redis):
        """Set up test environment"""
        self.mock_client = MagicMock()
        mock_redis.return_value = self.mock_client
        
        self.connector = RedisConnector()
    
    def test_set(self):
        """Test set method"""
        self.mock_client.set.return_value = True
        
        result = self.connector.set("test_key", "test_value")
        
        self.mock_client.set.assert_called_once()
        self.assertTrue(result)
    
    def test_set_with_dict(self):
        """Test set method with dict value"""
        self.mock_client.set.return_value = True
        
        test_dict = {"name": "test", "value": 123}
        result = self.connector.set("test_key", test_dict)
        
        self.mock_client.set.assert_called_once()
        # Check that the value was JSON serialized
        args, kwargs = self.mock_client.set.call_args
        self.assertEqual(args[0], "test_key")
        self.assertEqual(json.loads(args[1]), test_dict)
        self.assertTrue(result)
    
    def test_get(self):
        """Test get method"""
        self.mock_client.get.return_value = b"test_value"
        
        result = self.connector.get("test_key")
        
        self.mock_client.get.assert_called_once_with("test_key")
        self.assertEqual(result, "test_value")
    
    def test_get_with_json(self):
        """Test get method with JSON value"""
        test_dict = {"name": "test", "value": 123}
        self.mock_client.get.return_value = json.dumps(test_dict).encode()
        
        result = self.connector.get("test_key")
        
        self.mock_client.get.assert_called_once_with("test_key")
        self.assertEqual(result, test_dict)
    
    def test_delete(self):
        """Test delete method"""
        self.mock_client.delete.return_value = 1
        
        result = self.connector.delete("test_key")
        
        self.mock_client.delete.assert_called_once_with("test_key")
        self.assertEqual(result, 1)
    
    def test_publish(self):
        """Test publish method"""
        self.mock_client.publish.return_value = 1
        
        result = self.connector.publish("test_channel", "test_message")
        
        self.mock_client.publish.assert_called_once()
        self.assertEqual(result, 1)
    
    def test_publish_with_dict(self):
        """Test publish method with dict message"""
        self.mock_client.publish.return_value = 1
        
        test_dict = {"name": "test", "value": 123}
        result = self.connector.publish("test_channel", test_dict)
        
        self.mock_client.publish.assert_called_once()
        # Check that the message was JSON serialized
        args, kwargs = self.mock_client.publish.call_args
        self.assertEqual(args[0], "test_channel")
        self.assertEqual(json.loads(args[1]), test_dict)
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()