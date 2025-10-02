"""
Pytest configuration and fixtures for Net-Pulse tests.
"""

import pytest
from fastapi.testclient import TestClient

from netpulse.main import create_app


@pytest.fixture(scope="function")
def app(test_database_url, monkeypatch):
    """Create and configure a test instance of the FastAPI application."""
    from netpulse.database import set_db_path, initialize_database
    # Set database path first
    set_db_path(test_database_url)
    # Then initialize with the new path
    initialize_database()
    app = create_app()
    app.state.db_url = test_database_url
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client


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


@pytest.fixture(scope="function")
def test_database_url(tmp_path):
    """Provide a temporary database URL for each test function."""
    db_path = tmp_path / "test.db"
    return f"sqlite:///{db_path}"


@pytest.fixture(autouse=True)
def cleanup_database(test_database_url, monkeypatch):
    """Cleanup database before and after each test."""
    from netpulse.database import set_db_path, initialize_database
    import os

    # Ensure database file doesn't exist before test
    db_path = test_database_url.replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)

    # Set database path and initialize
    set_db_path(test_database_url)
    initialize_database()

    yield

    # Cleanup database file after test
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(autouse=True)
def cleanup_collector(monkeypatch):
    """Cleanup collector after each test."""
    import netpulse.collector

    # Reset collector instance before test
    netpulse.collector._collector_instance = None

    yield

    # Cleanup after test
    netpulse.collector._collector_instance = None