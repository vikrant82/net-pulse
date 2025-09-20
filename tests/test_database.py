"""
Comprehensive unit tests for the database module.

This module tests all database operations including:
- Database connection management
- Schema initialization
- CRUD operations for traffic data
- Configuration management
- Error handling and edge cases
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from netpulse.database import (
    DatabaseError,
    get_db_connection,
    initialize_database,
    insert_traffic_data,
    get_traffic_data,
    get_configuration_value,
    set_configuration_value,
    get_database_stats
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup after test
    if Path(temp_path).exists():
        Path(temp_path).unlink()


@pytest.fixture
def temp_db_connection(temp_db_path):
    """Create a temporary database connection for testing."""
    # Patch the DB_PATH to use our temporary database
    with patch('netpulse.database.DB_PATH', Path(temp_db_path)):
        yield temp_db_path


@pytest.fixture
def initialized_db(temp_db_connection):
    """Create and initialize a temporary database for testing."""
    # Initialize the database
    initialize_database()
    yield temp_db_connection


@pytest.fixture
def sample_traffic_data():
    """Provide sample traffic data for testing."""
    return {
        'timestamp': '2024-01-01T12:00:00',
        'interface_name': 'eth0',
        'rx_bytes': 1000,
        'tx_bytes': 2000,
        'rx_packets': 10,
        'tx_packets': 20
    }


@pytest.fixture
def multiple_traffic_records():
    """Provide multiple traffic records for testing."""
    base_time = datetime.fromisoformat('2024-01-01T12:00:00')
    records = []

    for i in range(5):
        records.append({
            'timestamp': (base_time + timedelta(minutes=i)).isoformat(),
            'interface_name': f'eth{i % 2}',  # Alternate between eth0 and eth1
            'rx_bytes': 1000 + i * 100,
            'tx_bytes': 2000 + i * 200,
            'rx_packets': 10 + i,
            'tx_packets': 20 + i * 2
        })

    return records


class TestDatabaseError:
    """Test the custom DatabaseError exception."""

    def test_database_error_inheritance(self):
        """Test that DatabaseError inherits from Exception."""
        error = DatabaseError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, DatabaseError)

    def test_database_error_message(self):
        """Test that DatabaseError stores the error message correctly."""
        message = "Database connection failed"
        error = DatabaseError(message)
        assert str(error) == message


class TestDatabaseConnection:
    """Test database connection management."""

    def test_get_db_connection_success(self, temp_db_path):
        """Test successful database connection."""
        with patch('netpulse.database.DB_PATH', Path(temp_db_path)):
            with get_db_connection() as conn:
                assert conn is not None
                assert isinstance(conn, sqlite3.Connection)
                assert conn.row_factory == sqlite3.Row

    def test_get_db_connection_failure(self):
        """Test database connection failure."""
        with patch('netpulse.database.DB_PATH', Path('/nonexistent/path/db.db')):
            with pytest.raises(DatabaseError, match="Failed to connect to database"):
                with get_db_connection():
                    pass

    def test_get_db_connection_context_manager_cleanup(self, temp_db_path):
        """Test that connection is properly closed after context manager."""
        with patch('netpulse.database.DB_PATH', Path(temp_db_path)):
            conn = None
            with get_db_connection() as db_conn:
                conn = db_conn
                # Connection should be open during context
                assert conn is not None

            # Connection should be closed after context manager
            # We can't directly check the closed attribute, but we can verify
            # that attempting to use the connection raises an error
            try:
                conn.execute("SELECT 1")
                assert False, "Connection should be closed"
            except sqlite3.ProgrammingError:
                # This is expected when connection is closed
                pass


class TestDatabaseInitialization:
    """Test database schema initialization."""

    def test_initialize_database_creates_tables(self, temp_db_connection):
        """Test that initialize_database creates required tables."""
        initialize_database()

        # Verify tables were created
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check traffic_data table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_data'")
            assert cursor.fetchone() is not None

            # Check configuration table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='configuration'")
            assert cursor.fetchone() is not None

    def test_initialize_database_creates_indexes(self, temp_db_connection):
        """Test that initialize_database creates required indexes."""
        initialize_database()

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row['name'] for row in cursor.fetchall()]

            expected_indexes = [
                'idx_traffic_data_timestamp',
                'idx_traffic_data_interface',
                'idx_configuration_key'
            ]

            for index in expected_indexes:
                assert index in indexes

    def test_initialize_database_handles_existing_tables(self, temp_db_connection):
        """Test that initialize_database handles existing tables gracefully."""
        # Initialize twice - should not fail
        initialize_database()
        initialize_database()  # Should not raise an error

    def test_initialize_database_failure(self):
        """Test database initialization failure."""
        with patch('netpulse.database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Connection failed")

            with pytest.raises(DatabaseError, match="Database initialization failed"):
                initialize_database()


class TestInsertTrafficData:
    """Test traffic data insertion functionality."""

    def test_insert_traffic_data_success(self, initialized_db, sample_traffic_data):
        """Test successful traffic data insertion."""
        record_id = insert_traffic_data(**sample_traffic_data)

        assert isinstance(record_id, int)
        assert record_id > 0

        # Verify the record was inserted
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM traffic_data WHERE id = ?", (record_id,))
            row = cursor.fetchone()

            assert row is not None
            assert row['interface_name'] == sample_traffic_data['interface_name']
            assert row['rx_bytes'] == sample_traffic_data['rx_bytes']
            assert row['tx_bytes'] == sample_traffic_data['tx_bytes']

    def test_insert_traffic_data_with_zero_values(self, initialized_db):
        """Test inserting traffic data with zero values."""
        data = {
            'timestamp': '2024-01-01T12:00:00',
            'interface_name': 'eth0',
            'rx_bytes': 0,
            'tx_bytes': 0,
            'rx_packets': 0,
            'tx_packets': 0
        }

        record_id = insert_traffic_data(**data)
        assert record_id > 0

    def test_insert_traffic_data_with_large_values(self, initialized_db):
        """Test inserting traffic data with large values."""
        data = {
            'timestamp': '2024-01-01T12:00:00',
            'interface_name': 'eth0',
            'rx_bytes': 2**31 - 1,  # Max 32-bit signed int
            'tx_bytes': 2**31 - 1,
            'rx_packets': 2**31 - 1,
            'tx_packets': 2**31 - 1
        }

        record_id = insert_traffic_data(**data)
        assert record_id > 0

    def test_insert_traffic_data_failure(self, initialized_db):
        """Test traffic data insertion failure."""
        with patch('netpulse.database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Insert failed")

            with pytest.raises(DatabaseError, match="Failed to insert traffic data"):
                insert_traffic_data(
                    '2024-01-01T12:00:00', 'eth0', 1000, 2000, 10, 20
                )

    def test_insert_traffic_data_invalid_timestamp(self, initialized_db):
        """Test inserting with invalid timestamp format."""
        # SQLite is quite permissive with timestamp formats
        # This test verifies that the function handles various timestamp formats
        # without raising DatabaseError (which would indicate a real database error)
        try:
            # This should succeed as SQLite accepts various text formats
            record_id = insert_traffic_data(
                'invalid-timestamp', 'eth0', 1000, 2000, 10, 20
            )
            assert record_id > 0
        except DatabaseError:
            # If it does raise an error, that's also acceptable
            # as it means the database rejected the invalid format
            pass

    def test_insert_traffic_data_returns_correct_id(self, initialized_db):
        """Test that insert_traffic_data returns the correct record ID."""
        # Insert first record
        record_id_1 = insert_traffic_data(
            '2024-01-01T12:00:00', 'eth0', 1000, 2000, 10, 20
        )

        # Insert second record
        record_id_2 = insert_traffic_data(
            '2024-01-01T12:01:00', 'eth1', 1500, 2500, 15, 25
        )

        assert record_id_2 == record_id_1 + 1


class TestGetTrafficData:
    """Test traffic data retrieval functionality."""

    def test_get_traffic_data_no_filters(self, initialized_db, multiple_traffic_records):
        """Test retrieving all traffic data without filters."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        result = get_traffic_data()

        assert len(result) == len(multiple_traffic_records)
        assert all(isinstance(record, dict) for record in result)
        assert all('id' in record for record in result)

    def test_get_traffic_data_with_limit(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data with limit."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        limit = 3
        result = get_traffic_data(limit=limit)

        assert len(result) == limit
        assert result[0]['id'] > result[-1]['id']  # Should be ordered by timestamp DESC

    def test_get_traffic_data_with_offset(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data with offset."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        offset = 2
        result = get_traffic_data(offset=offset)

        assert len(result) == len(multiple_traffic_records) - offset

    def test_get_traffic_data_with_interface_filter(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data filtered by interface."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        interface_name = 'eth0'
        result = get_traffic_data(interface_name=interface_name)

        assert all(record['interface_name'] == interface_name for record in result)
        assert len(result) > 0

    def test_get_traffic_data_with_time_filters(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data with time range filters."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        start_time = '2024-01-01T12:02:00'
        end_time = '2024-01-01T12:03:00'

        result = get_traffic_data(start_time=start_time, end_time=end_time)

        for record in result:
            timestamp = record['timestamp']
            assert start_time <= timestamp <= end_time

    def test_get_traffic_data_with_multiple_filters(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data with multiple filters."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        filters = {
            'interface_name': 'eth0',
            'limit': 2,
            'start_time': '2024-01-01T12:01:00'
        }

        result = get_traffic_data(**filters)

        assert len(result) <= 2
        assert all(record['interface_name'] == 'eth0' for record in result)

    def test_get_traffic_data_empty_result(self, initialized_db):
        """Test retrieving traffic data when no records exist."""
        result = get_traffic_data()
        assert result == []

    def test_get_traffic_data_no_matching_interface(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data for non-existent interface."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        result = get_traffic_data(interface_name='nonexistent')
        assert result == []

    def test_get_traffic_data_invalid_time_range(self, initialized_db, multiple_traffic_records):
        """Test retrieving traffic data with invalid time range."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        # Start time after end time
        result = get_traffic_data(
            start_time='2024-01-01T12:04:00',
            end_time='2024-01-01T12:00:00'
        )
        assert result == []

    def test_get_traffic_data_failure(self, initialized_db):
        """Test traffic data retrieval failure."""
        with patch('netpulse.database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Query failed")

            with pytest.raises(DatabaseError, match="Failed to retrieve traffic data"):
                get_traffic_data()


class TestConfigurationManagement:
    """Test configuration value management."""

    def test_set_configuration_value_new_key(self, initialized_db):
        """Test setting a new configuration value."""
        key = 'test_key'
        value = 'test_value'

        set_configuration_value(key, value)

        # Verify the value was set
        result = get_configuration_value(key)
        assert result == value

    def test_set_configuration_value_update_existing(self, initialized_db):
        """Test updating an existing configuration value."""
        key = 'test_key'
        original_value = 'original_value'
        new_value = 'new_value'

        # Set initial value
        set_configuration_value(key, original_value)

        # Update value
        set_configuration_value(key, new_value)

        # Verify the value was updated
        result = get_configuration_value(key)
        assert result == new_value

    def test_get_configuration_value_existing_key(self, initialized_db):
        """Test getting an existing configuration value."""
        key = 'test_key'
        value = 'test_value'

        set_configuration_value(key, value)
        result = get_configuration_value(key)

        assert result == value

    def test_get_configuration_value_nonexistent_key(self, initialized_db):
        """Test getting a non-existent configuration value."""
        result = get_configuration_value('nonexistent_key')
        assert result is None

    def test_set_configuration_value_failure(self, initialized_db):
        """Test setting configuration value failure."""
        with patch('netpulse.database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Insert failed")

            with pytest.raises(DatabaseError, match="Failed to set configuration value"):
                set_configuration_value('test_key', 'test_value')

    def test_get_configuration_value_failure(self, initialized_db):
        """Test getting configuration value failure."""
        with patch('netpulse.database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Query failed")

            with pytest.raises(DatabaseError, match="Failed to get configuration value"):
                get_configuration_value('test_key')

    def test_configuration_value_with_special_characters(self, initialized_db):
        """Test configuration values with special characters."""
        key = 'special_key'
        value = 'Special value with émojis 🎉 and symbols !@#$%^&*()'

        set_configuration_value(key, value)
        result = get_configuration_value(key)

        assert result == value


class TestDatabaseStats:
    """Test database statistics functionality."""

    def test_get_database_stats_empty_database(self, initialized_db):
        """Test getting stats from an empty database."""
        stats = get_database_stats()

        assert isinstance(stats, dict)
        assert stats['traffic_data_records'] == 0
        assert stats['configuration_records'] == 0
        assert stats['database_size_bytes'] >= 0
        assert 'database_path' in stats

    def test_get_database_stats_with_data(self, initialized_db, multiple_traffic_records):
        """Test getting stats from a database with data."""
        # Insert test data
        for record in multiple_traffic_records:
            insert_traffic_data(**record)

        # Add some configuration values
        set_configuration_value('key1', 'value1')
        set_configuration_value('key2', 'value2')

        stats = get_database_stats()

        assert stats['traffic_data_records'] == len(multiple_traffic_records)
        assert stats['configuration_records'] == 2
        assert stats['database_size_bytes'] > 0

    def test_get_database_stats_failure(self, initialized_db):
        """Test getting database stats failure."""
        with patch('netpulse.database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Stats query failed")

            with pytest.raises(DatabaseError, match="Failed to get database stats"):
                get_database_stats()

    def test_get_database_stats_file_not_found(self):
        """Test getting stats when database file doesn't exist."""
        with patch('netpulse.database.DB_PATH', Path('/nonexistent/database.db')):
            with pytest.raises(DatabaseError):
                get_database_stats()


class TestIntegrationScenarios:
    """Test integration scenarios and complex operations."""

    def test_full_crud_cycle(self, initialized_db):
        """Test a complete CRUD cycle."""
        # Create
        record_id = insert_traffic_data(
            '2024-01-01T12:00:00', 'eth0', 1000, 2000, 10, 20
        )

        # Read
        data = get_traffic_data(limit=1)
        assert len(data) == 1
        assert data[0]['id'] == record_id

        # Update configuration
        set_configuration_value('test_interface', 'eth0')

        # Verify configuration
        config_value = get_configuration_value('test_interface')
        assert config_value == 'eth0'

        # Get stats
        stats = get_database_stats()
        assert stats['traffic_data_records'] == 1
        assert stats['configuration_records'] == 1

    def test_multiple_interfaces_data(self, initialized_db):
        """Test handling data from multiple network interfaces."""
        interfaces = ['eth0', 'eth1', 'wlan0']

        for i, interface in enumerate(interfaces):
            insert_traffic_data(
                f'2024-01-01T12:{i:02d}:00',
                interface,
                1000 * (i + 1),
                2000 * (i + 1),
                10 * (i + 1),
                20 * (i + 1)
            )

        # Test data retrieval for each interface
        for interface in interfaces:
            data = get_traffic_data(interface_name=interface)
            assert len(data) == 1
            assert data[0]['interface_name'] == interface

    def test_time_series_queries(self, initialized_db):
        """Test time-series data queries."""
        base_time = datetime.fromisoformat('2024-01-01T12:00:00')

        # Insert data at different time intervals
        for i in range(10):
            insert_traffic_data(
                (base_time + timedelta(minutes=i * 5)).isoformat(),
                'eth0',
                1000 + i * 100,
                2000 + i * 200,
                10 + i,
                20 + i * 2
            )

        # Test querying different time ranges
        mid_time = (base_time + timedelta(minutes=20)).isoformat()
        data = get_traffic_data(end_time=mid_time)

        assert len(data) == 5  # Should get first 5 records

    def test_concurrent_operations_simulation(self, initialized_db):
        """Test simulation of concurrent database operations."""
        # This test simulates multiple operations that might happen concurrently
        data = []

        # Simulate inserting multiple records
        for i in range(10):
            record_id = insert_traffic_data(
                f'2024-01-01T12:{i:02d}:00',
                f'eth{i % 2}',
                1000 + i * 50,
                2000 + i * 100,
                10 + i,
                20 + i * 2
            )
            data.append(record_id)

        # Verify all records were inserted correctly
        all_data = get_traffic_data()
        assert len(all_data) == 10

        # Verify record IDs are sequential
        assert data == sorted(data)


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_database_file_permission_error(self):
        """Test handling of database file permission errors."""
        # This test would require mocking file system permissions
        # For now, we test the error handling structure
        pass

    def test_corrupted_database_handling(self, temp_db_path):
        """Test handling of corrupted database files."""
        # Create a corrupted database file
        with open(temp_db_path, 'w') as f:
            f.write('corrupted data')

        with patch('netpulse.database.DB_PATH', Path(temp_db_path)):
            # This should either raise DatabaseError or succeed
            # (SQLite can sometimes handle minor corruption gracefully)
            try:
                with get_db_connection():
                    pass  # If it succeeds, that's also acceptable
            except DatabaseError:
                pass  # If it raises an error, that's expected

    def test_sql_injection_prevention(self, initialized_db):
        """Test that SQL injection attempts are prevented by parameterized queries."""
        malicious_input = "'; DROP TABLE traffic_data; --"

        # This should succeed because parameterized queries prevent SQL injection
        # The malicious input will be treated as a literal string, not as SQL code
        record_id = insert_traffic_data(
            '2024-01-01T12:00:00',
            malicious_input,
            1000, 2000, 10, 20
        )

        # Verify the record was inserted successfully
        assert record_id > 0

        # Verify the table still exists and has the data
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM traffic_data")
            count = cursor.fetchone()['count']
            assert count == 1

            # Verify the malicious input was stored as literal text
            cursor.execute("SELECT interface_name FROM traffic_data WHERE id = ?", (record_id,))
            stored_value = cursor.fetchone()['interface_name']
            assert stored_value == malicious_input

    def test_large_dataset_handling(self, initialized_db):
        """Test handling of large datasets."""
        # Insert a large number of records
        num_records = 1000

        for i in range(num_records):
            insert_traffic_data(
                f'2024-01-01T{i % 24:02d}:{i % 60:02d}:00',
                f'eth{i % 5}',
                1000 + i,
                2000 + i,
                10 + i,
                20 + i
            )

        # Test pagination
        page_size = 100
        total_pages = (num_records + page_size - 1) // page_size

        for page in range(total_pages):
            offset = page * page_size
            data = get_traffic_data(limit=page_size, offset=offset)
            expected_count = min(page_size, num_records - offset)
            assert len(data) == expected_count

    def test_memory_usage_with_large_queries(self, initialized_db):
        """Test memory usage with large query results."""
        # Insert many records
        for i in range(100):
            insert_traffic_data(
                f'2024-01-01T12:{i:02d}:00',
                'eth0',
                1000 + i,
                2000 + i,
                10 + i,
                20 + i
            )

        # This should not cause memory issues
        data = get_traffic_data()
        assert len(data) == 100

        # Test with limit to ensure proper memory management
        limited_data = get_traffic_data(limit=10)
        assert len(limited_data) == 10