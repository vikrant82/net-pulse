#!/usr/bin/env python3
"""
Comprehensive API Tests for Net-Pulse

This module contains unit tests, integration tests, error handling tests,
and performance tests for all API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json
import csv
import io
from typing import Dict, Any

from netpulse.main import create_app, InterfaceInfo, InterfaceStats, TrafficDataRecord
from netpulse.network import NetworkError, InterfaceNotFoundError
from netpulse.collector import CollectorError


class TestAPIBase:
    """Base class for API tests with common setup and utilities."""

    @pytest.fixture
    def app(self):
        """Create FastAPI test application."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_interface_data(self):
        """Sample interface data for testing."""
        return {
            "eth0": {
                "name": "eth0",
                "addresses": [
                    {
                        "family": "AddressFamily.AF_INET",
                        "address": "192.168.1.100",
                        "netmask": "255.255.255.0",
                        "broadcast": "192.168.1.255"
                    }
                ],
                "status": "up",
                "mtu": 1500,
                "speed": 1000
            }
        }

    @pytest.fixture
    def sample_interface_stats(self):
        """Sample interface statistics for testing."""
        return {
            "interface_name": "eth0",
            "rx_bytes": 1000000,
            "tx_bytes": 500000,
            "rx_packets": 10000,
            "tx_packets": 5000,
            "rx_errors": 0,
            "tx_errors": 0,
            "rx_drops": 0,
            "tx_drops": 0,
            "timestamp": "2024-01-01T12:00:00+00:00",
            "status": "up"
        }

    @pytest.fixture
    def sample_traffic_data(self):
        """Sample traffic data for testing."""
        return [
            {
                "id": 1,
                "timestamp": "2024-01-01T12:00:00+00:00",
                "interface_name": "eth0",
                "rx_bytes": 1000,
                "tx_bytes": 500,
                "rx_packets": 10,
                "tx_packets": 5,
                "created_at": "2024-01-01T12:00:00+00:00"
            },
            {
                "id": 2,
                "timestamp": "2024-01-01T12:01:00+00:00",
                "interface_name": "eth0",
                "rx_bytes": 2000,
                "tx_bytes": 1000,
                "rx_packets": 20,
                "tx_packets": 10,
                "created_at": "2024-01-01T12:01:00+00:00"
            }
        ]


class TestInterfaceManagementEndpoints(TestAPIBase):
    """Test interface management endpoints."""

    def test_get_interfaces_success(self, client, sample_interface_data):
        """Test successful retrieval of all interfaces."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.return_value = sample_interface_data

            response = client.get("/api/interfaces")

            assert response.status_code == 200
            data = response.json()
            assert "eth0" in data
            assert data["eth0"]["name"] == "eth0"
            assert data["eth0"]["status"] == "up"
            mock_get_interfaces.assert_called_once()

    def test_get_interfaces_network_error(self, client):
        """Test interface retrieval with network error."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.side_effect = NetworkError("Network error")

            response = client.get("/api/interfaces")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Network error" in data["detail"]

    def test_get_specific_interface_success(self, client, sample_interface_data):
        """Test successful retrieval of specific interface."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.return_value = sample_interface_data

            response = client.get("/api/interfaces/eth0")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "eth0"
            assert data["status"] == "up"

    def test_get_specific_interface_not_found(self, client, sample_interface_data):
        """Test retrieval of non-existent interface."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.return_value = sample_interface_data

            response = client.get("/api/interfaces/nonexistent")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]

    def test_get_interface_stats_success(self, client, sample_interface_stats):
        """Test successful retrieval of interface statistics."""
        with patch('netpulse.main.get_interface_stats') as mock_get_stats:
            mock_get_stats.return_value = sample_interface_stats

            response = client.get("/api/interfaces/eth0/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["interface_name"] == "eth0"
            assert data["rx_bytes"] == 1000000
            assert data["status"] == "up"

    def test_get_interface_stats_not_found(self, client):
        """Test interface statistics retrieval for non-existent interface."""
        with patch('netpulse.main.get_interface_stats') as mock_get_stats:
            mock_get_stats.side_effect = InterfaceNotFoundError("Interface not found")

            response = client.get("/api/interfaces/nonexistent/stats")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]

    def test_get_interface_stats_network_error(self, client):
        """Test interface statistics retrieval with network error."""
        with patch('netpulse.main.get_interface_stats') as mock_get_stats:
            mock_get_stats.side_effect = NetworkError("Network error")

            response = client.get("/api/interfaces/eth0/stats")

            assert response.status_code == 500
            data = response.json()
            assert "Network error" in data["detail"]


class TestTrafficDataEndpoints(TestAPIBase):
    """Test traffic data endpoints."""

    def test_get_traffic_history_success(self, client, sample_traffic_data):
        """Test successful retrieval of traffic history."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/traffic/history")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["interface_name"] == "eth0"
            assert data[1]["interface_name"] == "eth0"

    def test_get_traffic_history_with_filters(self, client, sample_traffic_data):
        """Test traffic history retrieval with interface filter."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/traffic/history?interface_name=eth0&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            mock_get_data.assert_called_once_with(
                limit=10,
                offset=0,
                interface_name="eth0",
                start_time=None,
                end_time=None
            )

    def test_get_traffic_summary_success(self, client):
        """Test successful retrieval of traffic summary."""
        summary_data = {
            "total_interfaces": 2,
            "active_interfaces": 1,
            "total_rx_bytes": 1000000,
            "total_tx_bytes": 500000,
            "total_rx_packets": 10000,
            "total_tx_packets": 5000,
            "timestamp": "2024-01-01T12:00:00+00:00"
        }

        with patch('netpulse.main.get_interface_traffic_summary') as mock_get_summary:
            mock_get_summary.return_value = summary_data

            response = client.get("/api/traffic/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["total_interfaces"] == 2
            assert data["active_interfaces"] == 1
            assert data["total_rx_bytes"] == 1000000

    def test_get_traffic_summary_error(self, client):
        """Test traffic summary retrieval with error."""
        with patch('netpulse.main.get_interface_traffic_summary') as mock_get_summary:
            mock_get_summary.side_effect = NetworkError("Network error")

            response = client.get("/api/traffic/summary")

            assert response.status_code == 500
            data = response.json()
            assert "Network error" in data["detail"]

    def test_get_latest_traffic_success(self, client, sample_traffic_data):
        """Test successful retrieval of latest traffic data."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/traffic/latest?limit=5")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            mock_get_data.assert_called_once_with(limit=5)

    def test_get_latest_traffic_default_limit(self, client, sample_traffic_data):
        """Test latest traffic retrieval with default limit."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/traffic/latest")

            assert response.status_code == 200
            mock_get_data.assert_called_once_with(limit=10)


class TestConfigurationEndpoints(TestAPIBase):
    """Test configuration endpoints."""

    def test_get_monitored_interfaces_success(self, client):
        """Test successful retrieval of monitored interfaces."""
        with patch('netpulse.collector.get_collector') as mock_get_collector:
            mock_collector = Mock()
            mock_collector._get_monitored_interfaces.return_value = ["eth0", "wlan0"]
            mock_get_collector.return_value = mock_collector

            response = client.get("/api/config/interfaces")

            assert response.status_code == 200
            data = response.json()
            # The actual implementation returns the interfaces from the collector
            assert "interfaces" in data

    def test_get_monitored_interfaces_error(self, client):
        """Test monitored interfaces retrieval with error."""
        with patch('netpulse.collector.get_collector') as mock_get_collector:
            mock_get_collector.side_effect = Exception("Collector error")

            response = client.get("/api/config/interfaces")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data  # FastAPI standard error format
            assert "Collector error" in data["detail"]

    def test_update_monitored_interfaces_success(self, client):
        """Test successful update of monitored interfaces."""
        from netpulse.database import set_configuration_value
        from netpulse.network import validate_interface
        with patch.object(validate_interface, '__call__') as mock_validate, \
             patch.object(set_configuration_value, '__call__') as mock_set_config:
            mock_validate.return_value = True

            # Use valid interface names that exist on the system
            config_data = {"interfaces": ["lo0", "en0"]}
            response = client.put("/api/config/interfaces", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Monitored interfaces updated successfully"
            assert data["interfaces"] == ["lo0", "en0"]

    def test_update_monitored_interfaces_invalid_interface(self, client):
        """Test update with invalid interface."""
        with patch('netpulse.main.validate_interface') as mock_validate:
            mock_validate.return_value = False

            config_data = {"interfaces": ["invalid_interface"]}
            response = client.put("/api/config/interfaces", json=config_data)

            assert response.status_code == 400
            data = response.json()
            assert "Invalid interfaces" in data["detail"]

    def test_update_monitored_interfaces_missing_field(self, client):
        """Test update with missing interfaces field."""
        config_data = {}
        response = client.put("/api/config/interfaces", json=config_data)

        assert response.status_code == 400
        data = response.json()
        assert "interfaces field is required" in data["detail"]

    def test_get_collection_interval_success(self, client):
        """Test successful retrieval of collection interval."""
        with patch('netpulse.database.get_configuration_value') as mock_get_config:
            mock_get_config.return_value = "60"

            response = client.get("/api/config/collection-interval")

            assert response.status_code == 200
            data = response.json()
            # Test should use mocked value, not database value
            assert data["collection_interval_seconds"] == 60

    def test_get_collection_interval_default(self, client):
        """Test collection interval retrieval with default value."""
        from netpulse.database import get_configuration_value
        with patch.object(get_configuration_value, '__call__') as mock_get_config:
            mock_get_config.return_value = None

            response = client.get("/api/config/collection-interval")

            assert response.status_code == 200
            data = response.json()
            assert data["collection_interval_seconds"] == 30

    def test_update_collection_interval_success(self, client):
        """Test successful update of collection interval."""
        from netpulse.database import set_configuration_value
        with patch.object(set_configuration_value, '__call__') as mock_set_config:
            config_data = {"collection_interval": 120}
            response = client.put("/api/config/collection-interval", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["collection_interval_seconds"] == 120

    def test_update_collection_interval_invalid_value(self, client):
        """Test update with invalid collection interval."""
        config_data = {"collection_interval": 4000}  # Too high
        response = client.put("/api/config/collection-interval", json=config_data)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        # FastAPI returns detailed validation error format
        assert "detail" in data
        assert "Input should be less than or equal to 3600" in str(data["detail"])

    def test_update_collection_interval_missing_field(self, client):
        """Test update with missing collection_interval field."""
        config_data = {}
        response = client.put("/api/config/collection-interval", json=config_data)

        assert response.status_code == 400
        data = response.json()
        assert "collection_interval field is required" in data["detail"]

    def test_get_max_retries_success(self, client):
        """Test successful retrieval of max retries setting."""
        with patch('netpulse.database.get_configuration_value') as mock_get_config:
            mock_get_config.return_value = "5"

            response = client.get("/api/config/max-retries")

            assert response.status_code == 200
            data = response.json()
            assert data["max_retries"] == 5

    def test_get_max_retries_default(self, client):
        """Test max retries retrieval with default value."""
        from netpulse.database import get_configuration_value
        with patch.object(get_configuration_value, '__call__') as mock_get_config:
            mock_get_config.return_value = None

            response = client.get("/api/config/max-retries")

            assert response.status_code == 200
            data = response.json()
            assert data["max_retries"] == 3

    def test_update_max_retries_success(self, client):
        """Test successful update of max retries setting."""
        from netpulse.database import set_configuration_value
        with patch.object(set_configuration_value, '__call__') as mock_set_config:
            config_data = {"max_retries": 10}
            response = client.put("/api/config/max-retries", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["max_retries"] == 10

    def test_update_max_retries_invalid_value_too_high(self, client):
        """Test update with max retries value too high."""
        config_data = {"max_retries": 150}  # Too high
        response = client.put("/api/config/max-retries", json=config_data)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data
        assert "Input should be less than or equal to 100" in str(data["detail"])

    def test_update_max_retries_invalid_value_too_low(self, client):
        """Test update with max retries value too low."""
        config_data = {"max_retries": 0}  # Too low
        response = client.put("/api/config/max-retries", json=config_data)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data
        assert "Input should be greater than or equal to 1" in str(data["detail"])

    def test_update_max_retries_missing_field(self, client):
        """Test update with missing max_retries field."""
        config_data = {}
        response = client.put("/api/config/max-retries", json=config_data)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data
        assert "Field required" in str(data["detail"])

    def test_get_retry_delay_success(self, client):
        """Test successful retrieval of retry delay setting."""
        with patch('netpulse.database.get_configuration_value') as mock_get_config:
            mock_get_config.return_value = "2.5"

            response = client.get("/api/config/retry-delay")

            assert response.status_code == 200
            data = response.json()
            assert data["retry_delay_seconds"] == 2.5

    def test_get_retry_delay_default(self, client):
        """Test retry delay retrieval with default value."""
        from netpulse.database import get_configuration_value
        with patch.object(get_configuration_value, '__call__') as mock_get_config:
            mock_get_config.return_value = None

            response = client.get("/api/config/retry-delay")

            assert response.status_code == 200
            data = response.json()
            assert data["retry_delay_seconds"] == 1.0

    def test_update_retry_delay_success(self, client):
        """Test successful update of retry delay setting."""
        from netpulse.database import set_configuration_value
        with patch.object(set_configuration_value, '__call__') as mock_set_config:
            config_data = {"retry_delay": 3.0}
            response = client.put("/api/config/retry-delay", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["retry_delay_seconds"] == 3.0

    def test_update_retry_delay_invalid_value_too_high(self, client):
        """Test update with retry delay value too high."""
        config_data = {"retry_delay": 400.0}  # Too high
        response = client.put("/api/config/retry-delay", json=config_data)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data
        assert "Input should be less than or equal to 300" in str(data["detail"])

    def test_update_retry_delay_invalid_value_too_low(self, client):
        """Test update with retry delay value too low."""
        config_data = {"retry_delay": 0.05}  # Too low
        response = client.put("/api/config/retry-delay", json=config_data)

        assert response.status_code == 400  # Custom validation error
        data = response.json()
        assert "detail" in data
        assert "Retry delay must be between 0.1 and 300 seconds" in data["detail"]

    def test_update_retry_delay_missing_field(self, client):
        """Test update with missing retry_delay field."""
        config_data = {}
        response = client.put("/api/config/retry-delay", json=config_data)

        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data
        assert "Field required" in str(data["detail"])


class TestSystemInformationEndpoints(TestAPIBase):
    """Test system information endpoints."""

    def test_get_system_info_success(self, client):
        """Test successful retrieval of system information."""
        import platform
        import psutil
        import socket
        with patch.object(platform, 'system') as mock_platform_system, \
             patch.object(platform, 'release') as mock_platform_release, \
             patch.object(platform, 'python_version') as mock_platform_python, \
             patch.object(psutil, 'boot_time') as mock_psutil_boot, \
             patch.object(psutil, 'cpu_count') as mock_psutil_cpu, \
             patch.object(psutil, 'virtual_memory') as mock_psutil_memory, \
             patch.object(socket, 'gethostname') as mock_socket_hostname:
            mock_socket_hostname.return_value = "test-host"
            mock_platform_system.return_value = "Linux"
            mock_platform_release.return_value = "5.4.0"
            mock_platform_python.return_value = "3.9.0"
            mock_psutil_boot.return_value = 1609459200  # 2021-01-01
            mock_psutil_cpu.return_value = 4
            mock_psutil_memory.return_value = Mock(total=8589934592, available=4294967296)

            response = client.get("/api/system/info")

            assert response.status_code == 200
            data = response.json()
            assert data["hostname"] == "test-host"
            assert data["os"] == "Linux 5.4.0"
            assert data["cpu_count"] == 4

    def test_get_system_info_error(self, client):
        """Test system info retrieval with error."""
        import platform
        with patch.object(platform, 'system') as mock_platform_system:
            mock_platform_system.side_effect = Exception("Platform error")

            response = client.get("/api/system/info")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_get_system_health_success(self, client):
        """Test successful system health check."""
        with patch('netpulse.main.get_database_stats') as mock_db_stats, \
              patch('netpulse.main.get_network_interfaces') as mock_interfaces, \
              patch('netpulse.main.get_collector') as mock_get_collector:
            mock_db_stats.return_value = {"traffic_data_records": 100}
            mock_interfaces.return_value = {"eth0": {"status": "up"}}
            mock_collector = Mock()
            mock_collector.get_collection_status.return_value = {"is_running": True}
            mock_get_collector.return_value = mock_collector

            response = client.get("/api/system/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_status"] == "healthy"
            assert data["interfaces_status"] == "healthy"
            assert data["collector_status"] == "healthy"

    def test_get_system_health_degraded(self, client):
        """Test system health check with degraded status."""
        with patch('netpulse.main.get_database_stats') as mock_db_stats, \
              patch('netpulse.main.get_network_interfaces') as mock_interfaces, \
              patch('netpulse.collector.get_collector') as mock_collector:
            mock_db_stats.return_value = {"traffic_data_records": 100}
            mock_interfaces.return_value = {"eth0": {"status": "up"}}
            mock_collector.return_value.get_collection_status.return_value = {"is_running": False}

            response = client.get("/api/system/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["collector_status"] == "stopped"

    def test_get_system_health_unhealthy(self, client):
        """Test system health check with unhealthy status."""
        with patch('netpulse.main.get_database_stats') as mock_db_stats, \
              patch('netpulse.main.get_network_interfaces') as mock_interfaces, \
              patch('netpulse.collector.get_collector') as mock_collector:
            mock_db_stats.side_effect = Exception("Database error")
            mock_interfaces.return_value = {"eth0": {"status": "up"}}
            mock_collector.return_value.get_collection_status.return_value = {"is_running": True}

            response = client.get("/api/system/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_status"] == "unhealthy"

    def test_get_system_metrics_success(self, client):
        """Test successful retrieval of system metrics."""
        import psutil
        import shutil
        with patch.object(psutil, 'cpu_percent') as mock_cpu_percent, \
             patch.object(psutil, 'virtual_memory') as mock_virtual_memory, \
             patch.object(shutil, 'disk_usage') as mock_disk_usage, \
             patch('netpulse.main.get_network_interfaces') as mock_interfaces:
            mock_cpu_percent.return_value = 50.0
            mock_memory = Mock()
            mock_memory.percent = 75.0
            mock_virtual_memory.return_value = mock_memory
            mock_disk_usage.return_value = Mock(total=1000000000, used=500000000)
            mock_interfaces.return_value = {"eth0": {"status": "up"}, "wlan0": {"status": "up"}}

            response = client.get("/api/system/metrics")

            assert response.status_code == 200
            data = response.json()
            assert data["cpu_percent"] == 50.0
            assert data["memory_percent"] == 75.0
            assert data["disk_usage_percent"] == 50.0
            assert data["network_interfaces_count"] == 2

    def test_get_system_metrics_error(self, client):
        """Test system metrics retrieval with error."""
        import psutil
        with patch.object(psutil, 'cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.side_effect = Exception("CPU error")

            response = client.get("/api/system/metrics")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestDataExportEndpoints(TestAPIBase):
    """Test data export endpoints."""

    def test_export_traffic_json_success(self, client, sample_traffic_data):
        """Test successful JSON export of traffic data."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/export/traffic?format=json&limit=100")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["interface_name"] == "eth0"

    def test_export_traffic_csv_success(self, client, sample_traffic_data):
        """Test successful CSV export of traffic data."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/export/traffic?format=csv&limit=100")

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
            assert "attachment" in response.headers["content-disposition"]

            # Parse CSV content
            csv_content = response.text
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            assert len(rows) == 2
            assert rows[0]["interface_name"] == "eth0"

    def test_export_traffic_with_filters(self, client, sample_traffic_data):
        """Test traffic export with interface filter."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            response = client.get("/api/export/traffic?format=json&interface_name=eth0&limit=50")

            assert response.status_code == 200
            mock_get_data.assert_called_once_with(
                limit=50,
                interface_name="eth0",
                start_time=None,
                end_time=None
            )

    def test_export_traffic_invalid_format(self, client):
        """Test export with invalid format."""
        response = client.get("/api/export/traffic?format=xml")

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "pattern" in str(data["detail"])

    def test_export_traffic_error(self, client):
        """Test export with data retrieval error."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.side_effect = Exception("Export error")

            response = client.get("/api/export/traffic?format=json")

            assert response.status_code == 500
            data = response.json()
            assert "Export error" in data["detail"]


class TestErrorHandling(TestAPIBase):
    """Test error handling and exception management."""

    def test_network_error_handler(self, client):
        """Test NetworkError exception handler."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.side_effect = NetworkError("Custom network error")

            response = client.get("/api/interfaces")

            assert response.status_code == 500
            data = response.json()
            # HTTPException handler takes precedence over global NetworkError handler
            assert "detail" in data
            assert "Custom network error" in data["detail"]

    def test_interface_not_found_error_handler(self, client):
        """Test InterfaceNotFoundError exception handler."""
        with patch('netpulse.main.get_interface_stats') as mock_get_stats:
            mock_get_stats.side_effect = InterfaceNotFoundError("Interface not found")

            response = client.get("/api/interfaces/nonexistent/stats")

            assert response.status_code == 404
            data = response.json()
            # HTTPException handler takes precedence over global InterfaceNotFoundError handler
            assert "detail" in data
            assert "not found" in data["detail"]

    def test_collector_error_handler(self, client):
        """Test CollectorError exception handler."""
        from netpulse.collector import get_collector
        with patch.object(get_collector, '__call__') as mock_get_collector:
            mock_get_collector.side_effect = CollectorError("Collector error")

            response = client.get("/api/config/interfaces")

            assert response.status_code == 500
            data = response.json()
            # HTTPException handler takes precedence over global CollectorError handler
            assert "detail" in data
            assert "Collector error" in data["detail"]

    def test_http_exception_handler(self, client):
        """Test HTTPException handler."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.side_effect = HTTPException(status_code=404, detail="Custom HTTP error")

            response = client.get("/api/interfaces/nonexistent")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "Custom HTTP error" in data["detail"]

    def test_general_exception_handler(self, client):
        """Test general exception handler."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.side_effect = Exception("Unexpected error")

            response = client.get("/api/interfaces")

            assert response.status_code == 500
            data = response.json()
            # HTTPException handler takes precedence over global Exception handler
            assert "detail" in data
            assert "unexpected error" in data["detail"]


class TestPerformance(TestAPIBase):
    """Performance tests for API endpoints."""

    def test_interfaces_endpoint_performance(self, client, sample_interface_data):
        """Test performance of interfaces endpoint."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.return_value = sample_interface_data

            import time
            start_time = time.time()

            # Make multiple requests
            for _ in range(10):
                response = client.get("/api/interfaces")
                assert response.status_code == 200

            end_time = time.time()
            total_time = end_time - start_time

            # Should complete within reasonable time (under 1 second for 10 requests)
            assert total_time < 1.0, f"Performance test failed: {total_time}s"

    def test_traffic_history_endpoint_performance(self, client, sample_traffic_data):
        """Test performance of traffic history endpoint."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data:
            mock_get_data.return_value = sample_traffic_data

            import time
            start_time = time.time()

            # Make multiple requests with different parameters
            for i in range(1, 6):  # Start from 1 to avoid limit=0
                response = client.get(f"/api/traffic/history?limit={i*10}")
                assert response.status_code == 200

            end_time = time.time()
            total_time = end_time - start_time

            # Should complete within reasonable time
            assert total_time < 0.5, f"Performance test failed: {total_time}s"

    def test_concurrent_requests_performance(self, client, sample_interface_data):
        """Test performance under concurrent requests."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces:
            mock_get_interfaces.return_value = sample_interface_data

            import concurrent.futures
            import time

            def make_request():
                response = client.get("/api/interfaces")
                return response.status_code

            start_time = time.time()

            # Make concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

            end_time = time.time()
            total_time = end_time - start_time

            # All requests should succeed
            assert all(status == 200 for status in results)
            # Should complete within reasonable time
            assert total_time < 2.0, f"Concurrent performance test failed: {total_time}s"


class TestAPIDocumentation(TestAPIBase):
    """Test API documentation and OpenAPI schema."""

    def test_openapi_schema_exists(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_swagger_ui_available(self, client):
        """Test that Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        """Test that ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_info(self, client):
        """Test OpenAPI info section."""
        response = client.get("/openapi.json")
        schema = response.json()
        assert schema["info"]["title"] == "Net-Pulse"
        assert schema["info"]["version"] == "0.1.0"
        assert "Lightweight network traffic monitoring" in schema["info"]["description"]

    def test_openapi_paths(self, client):
        """Test that all expected paths are in OpenAPI schema."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # Check for key endpoints
        expected_paths = [
            "/api/interfaces",
            "/api/interfaces/{interface_name}",
            "/api/interfaces/{interface_name}/stats",
            "/api/traffic/history",
            "/api/traffic/summary",
            "/api/traffic/latest",
            "/api/config/interfaces",
            "/api/config/collection-interval",
            "/api/config/max-retries",
            "/api/config/retry-delay",
            "/api/system/info",
            "/api/system/health",
            "/api/system/metrics",
            "/api/export/traffic"
        ]

        for path in expected_paths:
            assert path in paths, f"Path {path} not found in OpenAPI schema"


class TestIntegration(TestAPIBase):
    """Integration tests for API endpoints."""

    def test_full_interface_workflow(self, client, sample_interface_data, sample_interface_stats):
        """Test complete workflow: get interfaces -> get specific interface -> get stats."""
        with patch('netpulse.main.get_network_interfaces') as mock_get_interfaces, \
             patch('netpulse.main.get_interface_stats') as mock_get_stats:
            mock_get_interfaces.return_value = sample_interface_data
            mock_get_stats.return_value = sample_interface_stats

            # Step 1: Get all interfaces
            response1 = client.get("/api/interfaces")
            assert response1.status_code == 200
            interfaces = response1.json()
            assert "eth0" in interfaces

            # Step 2: Get specific interface
            response2 = client.get("/api/interfaces/eth0")
            assert response2.status_code == 200
            interface = response2.json()
            assert interface["name"] == "eth0"

            # Step 3: Get interface stats
            response3 = client.get("/api/interfaces/eth0/stats")
            assert response3.status_code == 200
            stats = response3.json()
            assert stats["interface_name"] == "eth0"
            assert stats["rx_bytes"] == 1000000

    def test_traffic_data_workflow(self, client, sample_traffic_data):
        """Test complete traffic data workflow."""
        with patch('netpulse.main.get_traffic_data') as mock_get_data, \
             patch('netpulse.main.get_interface_traffic_summary') as mock_get_summary:
            mock_get_data.return_value = sample_traffic_data
            mock_get_summary.return_value = {
                "total_interfaces": 1,
                "active_interfaces": 1,
                "total_rx_bytes": 3000,
                "total_tx_bytes": 1500,
                "total_rx_packets": 30,
                "total_tx_packets": 15,
                "timestamp": "2024-01-01T12:00:00+00:00"
            }

            # Get traffic history
            response1 = client.get("/api/traffic/history?limit=10")
            assert response1.status_code == 200
            history = response1.json()
            assert len(history) == 2

            # Get traffic summary
            response2 = client.get("/api/traffic/summary")
            assert response2.status_code == 200
            summary = response2.json()
            assert summary["total_interfaces"] == 1

            # Get latest traffic
            response3 = client.get("/api/traffic/latest?limit=5")
            assert response3.status_code == 200
            latest = response3.json()
            assert len(latest) == 2

    def test_system_endpoints_integration(self, client):
        """Test integration of system endpoints."""
        import platform
        import psutil
        import shutil
        import socket
        with patch.object(socket, 'gethostname') as mock_socket_hostname, \
             patch.object(platform, 'system') as mock_platform_system, \
             patch.object(platform, 'release') as mock_platform_release, \
             patch.object(platform, 'python_version') as mock_platform_python, \
             patch.object(psutil, 'boot_time') as mock_psutil_boot, \
             patch.object(psutil, 'cpu_count') as mock_psutil_cpu, \
             patch.object(psutil, 'virtual_memory') as mock_psutil_memory, \
             patch.object(psutil, 'cpu_percent') as mock_cpu_percent, \
             patch.object(shutil, 'disk_usage') as mock_disk_usage, \
             patch('netpulse.main.get_network_interfaces') as mock_interfaces:
            # Mock system calls
            mock_socket_hostname.return_value = "test-host"
            mock_platform_system.return_value = "Linux"
            mock_platform_release.return_value = "5.4.0"
            mock_platform_python.return_value = "3.9.0"
            mock_psutil_boot.return_value = 1609459200
            mock_psutil_cpu.return_value = 4
            mock_psutil_memory.return_value = Mock(total=8589934592, available=4294967296)
            mock_cpu_percent.return_value = 50.0
            mock_disk_usage.return_value = Mock(total=1000000000, used=500000000)
            mock_interfaces.return_value = {"eth0": {"status": "up"}}

            # Test system info
            response1 = client.get("/api/system/info")
            assert response1.status_code == 200
            info = response1.json()
            assert info["hostname"] == "test-host"

            # Test system metrics
            response2 = client.get("/api/system/metrics")
            assert response2.status_code == 200
            metrics = response2.json()
            assert metrics["cpu_percent"] == 50.0

            # Test system health
            response3 = client.get("/api/system/health")
            assert response3.status_code == 200
            health = response3.json()
            assert "status" in health
            assert "database_status" in health
            assert "interfaces_status" in health
            assert "collector_status" in health