"""
Tests for test utilities and helper functions.
"""

import pytest

from tests.test_utils import (
    TestDataFactory,
    APITestHelper,
    MockNetworkInterface,
    PerformanceTestHelper,
    create_test_client_with_auth,
    validate_uuid_format,
    assert_valid_timestamp
)


class TestTestDataFactory:
    """Test the TestDataFactory class."""

    def test_create_network_stats_default(self):
        """Test creating network stats with default values."""
        factory = TestDataFactory()
        data = factory.create_network_stats()

        assert data["bytes_sent"] == 1024
        assert data["bytes_recv"] == 2048
        assert data["packets_sent"] == 10
        assert data["packets_recv"] == 15
        assert data["timestamp"] == "2024-01-01T12:00:00Z"

    def test_create_network_stats_custom(self):
        """Test creating network stats with custom values."""
        factory = TestDataFactory()
        data = factory.create_network_stats(
            bytes_sent=5000,
            bytes_recv=10000,
            packets_sent=25,
            packets_recv=50,
            timestamp="2024-01-02T13:00:00Z"
        )

        assert data["bytes_sent"] == 5000
        assert data["bytes_recv"] == 10000
        assert data["packets_sent"] == 25
        assert data["packets_recv"] == 50
        assert data["timestamp"] == "2024-01-02T13:00:00Z"

    def test_create_interface_info_default(self):
        """Test creating interface info with default values."""
        factory = TestDataFactory()
        info = factory.create_interface_info()

        assert info["name"] == "eth0"
        assert info["status"] == "up"
        assert info["speed"] == 1000
        assert info["mtu"] == 1500

    def test_create_interface_info_custom(self):
        """Test creating interface info with custom values."""
        factory = TestDataFactory()
        info = factory.create_interface_info(
            name="wlan0",
            status="down",
            speed=100,
            mtu=1400
        )

        assert info["name"] == "wlan0"
        assert info["status"] == "down"
        assert info["speed"] == 100
        assert info["mtu"] == 1400


class TestMockNetworkInterface:
    """Test the MockNetworkInterface class."""

    def test_mock_interface_creation(self):
        """Test creating a mock network interface."""
        interface = MockNetworkInterface("eth0")

        assert interface.name == "eth0"
        assert interface.bytes_sent == 1000
        assert interface.bytes_recv == 2000
        assert interface.packets_sent == 50
        assert interface.packets_recv == 75

    def test_get_stats(self):
        """Test getting statistics from mock interface."""
        interface = MockNetworkInterface("eth0")
        stats = interface.get_stats()

        expected_stats = {
            "bytes_sent": 1000,
            "bytes_recv": 2000,
            "packets_sent": 50,
            "packets_recv": 75
        }
        assert stats == expected_stats

    def test_update_stats(self):
        """Test updating statistics on mock interface."""
        interface = MockNetworkInterface("eth0")

        interface.update_stats(bytes_sent=3000, bytes_recv=4000)

        assert interface.bytes_sent == 3000
        assert interface.bytes_recv == 4000
        assert interface.packets_sent == 50  # Should remain unchanged
        assert interface.packets_recv == 75  # Should remain unchanged

    def test_update_stats_partial(self):
        """Test updating only some statistics."""
        interface = MockNetworkInterface("eth0")

        interface.update_stats(bytes_sent=5000)

        assert interface.bytes_sent == 5000
        assert interface.bytes_recv == 2000  # Should remain unchanged


class TestPerformanceTestHelper:
    """Test the PerformanceTestHelper class."""

    def test_time_function(self):
        """Test timing a function execution."""
        helper = PerformanceTestHelper()

        def sample_function(x, y):
            return x + y

        result, duration = helper.time_function(sample_function, 2, 3)

        assert result == 5
        assert duration >= 0  # Duration should be non-negative
        assert duration < 1  # Should be very fast for this simple function

    def test_assert_performance_threshold_pass(self):
        """Test performance threshold assertion when it should pass."""
        helper = PerformanceTestHelper()

        # This should not raise an exception
        helper.assert_performance_threshold(0.5, 1.0)

    def test_assert_performance_threshold_fail(self):
        """Test performance threshold assertion when it should fail."""
        helper = PerformanceTestHelper()

        with pytest.raises(AssertionError, match="Function took"):
            helper.assert_performance_threshold(1.5, 1.0)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_validate_uuid_format_valid(self):
        """Test UUID format validation with valid UUID."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert validate_uuid_format(valid_uuid) is True

    def test_validate_uuid_format_invalid(self):
        """Test UUID format validation with invalid UUID."""
        invalid_uuid = "not-a-uuid"
        assert validate_uuid_format(invalid_uuid) is False

    def test_assert_valid_timestamp_valid(self):
        """Test timestamp validation with valid timestamp."""
        valid_timestamp = "2024-01-01T12:00:00Z"
        # Should not raise an exception
        assert_valid_timestamp(valid_timestamp)

    def test_assert_valid_timestamp_invalid(self):
        """Test timestamp validation with invalid timestamp."""
        invalid_timestamp = "not-a-timestamp"
        with pytest.raises(AssertionError, match="Invalid timestamp format"):
            assert_valid_timestamp(invalid_timestamp)

    def test_create_test_client_with_auth(self):
        """Test creating test client with authentication."""
        from unittest.mock import Mock

        mock_client = Mock()
        mock_client.headers = {}

        result = create_test_client_with_auth(mock_client, "test-token")

        assert result == mock_client
        assert mock_client.headers["Authorization"] == "Bearer test-token"