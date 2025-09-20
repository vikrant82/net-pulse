"""
Test utilities and helper functions for Net-Pulse tests.
"""

import json
import time
from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest


class TestDataFactory:
    """Factory class for creating test data."""

    @staticmethod
    def create_network_stats(
        bytes_sent: int = 1024,
        bytes_recv: int = 2048,
        packets_sent: int = 10,
        packets_recv: int = 15,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create sample network statistics data."""
        if timestamp is None:
            timestamp = "2024-01-01T12:00:00Z"

        return {
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "packets_sent": packets_sent,
            "packets_recv": packets_recv,
            "timestamp": timestamp
        }

    @staticmethod
    def create_interface_info(
        name: str = "eth0",
        status: str = "up",
        speed: int = 1000,
        mtu: int = 1500
    ) -> Dict[str, Any]:
        """Create sample network interface information."""
        return {
            "name": name,
            "status": status,
            "speed": speed,
            "mtu": mtu
        }


class APITestHelper:
    """Helper class for API testing."""

    @staticmethod
    def assert_json_response(response, expected_status: int = 200):
        """Assert that response is valid JSON with expected status."""
        assert response.status_code == expected_status
        assert "application/json" in response.headers.get("content-type", "")

        # Try to parse JSON to ensure it's valid
        json.loads(response.content)

    @staticmethod
    def assert_health_response(response):
        """Assert that response is a valid health check response."""
        APITestHelper.assert_json_response(response, 200)
        data = response.json()
        assert data["status"] == "healthy"

    @staticmethod
    def assert_error_response(response, expected_status: int = 400):
        """Assert that response is a valid error response."""
        APITestHelper.assert_json_response(response, expected_status)
        data = response.json()
        assert "detail" in data or "error" in data


class MockNetworkInterface:
    """Mock network interface for testing."""

    def __init__(self, name: str = "eth0"):
        self.name = name
        self.bytes_sent = 1000
        self.bytes_recv = 2000
        self.packets_sent = 50
        self.packets_recv = 75

    def get_stats(self) -> Dict[str, int]:
        """Get mock network statistics."""
        return {
            "bytes_sent": self.bytes_sent,
            "bytes_recv": self.bytes_recv,
            "packets_sent": self.packets_sent,
            "packets_recv": self.packets_recv
        }

    def update_stats(self, bytes_sent: Optional[int] = None, bytes_recv: Optional[int] = None):
        """Update mock statistics."""
        if bytes_sent is not None:
            self.bytes_sent = bytes_sent
        if bytes_recv is not None:
            self.bytes_recv = bytes_recv


class PerformanceTestHelper:
    """Helper class for performance testing."""

    @staticmethod
    def time_function(func, *args, **kwargs):
        """Time a function execution."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    @staticmethod
    def assert_performance_threshold(duration: float, max_duration: float = 1.0):
        """Assert that function execution is within performance threshold."""
        assert duration <= max_duration, f"Function took {duration:.2f}s, expected <= {max_duration}s"


# Test fixtures for utilities
@pytest.fixture
def test_data_factory():
    """Provide TestDataFactory instance."""
    return TestDataFactory()


@pytest.fixture
def api_helper():
    """Provide APITestHelper instance."""
    return APITestHelper()


@pytest.fixture
def mock_interface():
    """Provide MockNetworkInterface instance."""
    return MockNetworkInterface()


@pytest.fixture
def performance_helper():
    """Provide PerformanceTestHelper instance."""
    return PerformanceTestHelper()


# Utility functions for tests
def create_test_client_with_auth(client, token: str = "test-token"):
    """Create a test client with authentication header."""
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def validate_uuid_format(uuid_string: str) -> bool:
    """Validate UUID format."""
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_string.lower()))


def assert_valid_timestamp(timestamp: str):
    """Assert that timestamp is in valid ISO format."""
    import re
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$'
    assert re.match(iso_pattern, timestamp), f"Invalid timestamp format: {timestamp}"