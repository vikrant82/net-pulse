"""
Pytest configuration and fixtures for Net-Pulse tests.
"""

import pytest
from fastapi.testclient import TestClient

from netpulse.main import create_app


@pytest.fixture
def app():
    """Create and configure a test instance of the FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_network_data():
    """Provide sample network data for testing."""
    return {
        "bytes_sent": 1024,
        "bytes_recv": 2048,
        "packets_sent": 10,
        "packets_recv": 15,
        "timestamp": "2024-01-01T12:00:00Z"
    }


@pytest.fixture
def mock_network_interface():
    """Provide mock network interface data for testing."""
    return {
        "name": "eth0",
        "status": "up",
        "speed": 1000,
        "mtu": 1500
    }


@pytest.fixture(scope="session")
def test_database_url():
    """Provide a test database URL."""
    return "sqlite:///./test.db"


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Add any cleanup logic here if needed
    # For example, cleaning up temporary files, database records, etc.


# Custom markers for test categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.integration,
    pytest.mark.api
]