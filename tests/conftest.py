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
    # Clean up global collector instance to prevent test interference
    try:
        from netpulse.collector import _collector_instance, _collector_lock
        with _collector_lock:
            if _collector_instance is not None:
                try:
                    _collector_instance.stop_collection()
                except Exception:
                    pass  # Ignore errors during cleanup
                _collector_instance = None
    except Exception:
        pass  # Ignore import errors during cleanup

    # Clean up database records created during tests
    try:
        from netpulse.database import get_db_connection, DatabaseError
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Clear traffic data and reset configuration to defaults
            cursor.execute("DELETE FROM traffic_data")
            cursor.execute("""
                UPDATE configuration
                SET value = CASE
                    WHEN key = 'collector.polling_interval' THEN '30'
                    WHEN key = 'collector.max_retries' THEN '3'
                    WHEN key = 'collector.retry_delay' THEN '1.0'
                    WHEN key = 'collector.monitored_interfaces' THEN ''
                    ELSE value
                END
            """)
            # Insert default configuration if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO configuration (key, value) VALUES
                ('collector.polling_interval', '30'),
                ('collector.max_retries', '3'),
                ('collector.retry_delay', '1.0'),
                ('collector.monitored_interfaces', '')
            """)
            conn.commit()
    except Exception:
        pass  # Ignore database cleanup errors


# Custom markers for test categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.integration,
    pytest.mark.api
]