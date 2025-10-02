#!/usr/bin/env python3
"""
Net-Pulse Database Module

This module handles all database operations for Net-Pulse, including:
- SQLite database connection and initialization
- Schema creation for traffic_data and configuration tables
- CRUD operations for network traffic data and configuration settings
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path - created in project root
DB_PATH = Path(__file__).parent.parent.parent / "netpulse.db"

def get_db_path():
    """Get the current database path."""
    return DB_PATH

def set_db_path(path):
    """Set the database path for testing."""
    global DB_PATH, _initialized
    # Handle sqlite:// URLs by stripping the prefix
    if path.startswith("sqlite:///"):
        path = path[10:]  # Remove 'sqlite:///' prefix
    DB_PATH = Path(path)
    # Reset initialization flag when path changes so new database gets initialized
    _initialized = False
    # Initialize the new database immediately
    try:
        initialize_database()
    except DatabaseError as e:
        logger.error(f"Failed to initialize database after path change: {e}")
        # Don't raise the exception to allow tests to continue


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


@contextmanager
def get_db_connection(db_url: Optional[str] = None):
    """
    Context manager for database connections.

    Yields:
        sqlite3.Connection: Database connection object

    Raises:
        DatabaseError: If connection fails
    """
    conn = None
    # Use the dynamic DB_PATH if no specific URL provided
    if db_url is None:
        db_to_connect = str(DB_PATH)
    else:
        db_to_connect = db_url

    if db_to_connect.startswith("sqlite:///"):
        db_to_connect = db_to_connect[10:]
    try:
        conn = sqlite3.connect(db_to_connect)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise DatabaseError(f"Failed to connect to database: {e}")
    finally:
        if conn:
            conn.close()


def initialize_database(db_url: Optional[str] = None) -> None:
    """
    Initialize the database by creating tables if they don't exist.

    Creates:
        - traffic_data table with network traffic information
        - configuration table for key-value configuration settings

    Raises:
        DatabaseError: If table creation fails
    """
    try:
        # Use the provided URL or get it from the current DB_PATH
        if db_url is None:
            db_to_connect = str(DB_PATH)
        else:
            db_to_connect = db_url

        with get_db_connection(db_to_connect) as conn:
            cursor = conn.cursor()

            # Create traffic_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    interface_name TEXT NOT NULL,
                    rx_bytes INTEGER NOT NULL DEFAULT 0,
                    tx_bytes INTEGER NOT NULL DEFAULT 0,
                    rx_packets INTEGER NOT NULL DEFAULT 0,
                    tx_packets INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_traffic_data_timestamp
                ON traffic_data(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_traffic_data_interface
                ON traffic_data(interface_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_configuration_key
                ON configuration(key)
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Database initialization failed: {e}")


def insert_traffic_data(
    timestamp: str,
    interface_name: str,
    rx_bytes: int,
    tx_bytes: int,
    rx_packets: int,
    tx_packets: int
) -> int:
    """
    Insert a new traffic data record.

    Args:
        timestamp: ISO format timestamp string
        interface_name: Network interface name (e.g., 'eth0', 'wlan0')
        rx_bytes: Received bytes count
        tx_bytes: Transmitted bytes count
        rx_packets: Received packets count
        tx_packets: Transmitted packets count

    Returns:
        int: ID of the inserted record

    Raises:
        DatabaseError: If insertion fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO traffic_data (
                    timestamp, interface_name, rx_bytes, tx_bytes,
                    rx_packets, tx_packets
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, interface_name, rx_bytes, tx_bytes, rx_packets, tx_packets))

            conn.commit()
            record_id = cursor.lastrowid
            if record_id is None:
                raise DatabaseError("Failed to get record ID after insertion")
            logger.debug(f"Inserted traffic data record with ID: {record_id}")
            return record_id

    except sqlite3.Error as e:
        logger.error(f"Failed to insert traffic data: {e}")
        raise DatabaseError(f"Failed to insert traffic data: {e}")


def get_traffic_data(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    interface_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve traffic data with optional filtering.

    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        interface_name: Filter by specific interface name
        start_time: Filter records from this timestamp (ISO format)
        end_time: Filter records until this timestamp (ISO format)

    Returns:
        List[Dict[str, Any]]: List of traffic data records

    Raises:
        DatabaseError: If query fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Build query dynamically based on filters
            query = """
                SELECT id, timestamp, interface_name, rx_bytes, tx_bytes,
                       rx_packets, tx_packets, created_at
                FROM traffic_data
                WHERE 1=1
            """

            params = []

            if interface_name:
                query += " AND interface_name = ?"
                params.append(interface_name)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            query += " ORDER BY timestamp DESC"

            if limit:
                if offset:
                    query += " LIMIT ? OFFSET ?"
                    params.append(limit)
                    params.append(offset)
                else:
                    query += " LIMIT ?"
                    params.append(limit)
            elif offset:
                query += " LIMIT -1 OFFSET ?"
                params.append(offset)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert rows to list of dictionaries
            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'interface_name': row['interface_name'],
                    'rx_bytes': row['rx_bytes'],
                    'tx_bytes': row['tx_bytes'],
                    'rx_packets': row['rx_packets'],
                    'tx_packets': row['tx_packets'],
                    'created_at': row['created_at']
                })

            logger.debug(f"Retrieved {len(result)} traffic data records")
            return result

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve traffic data: {e}")
        raise DatabaseError(f"Failed to retrieve traffic data: {e}")


def get_configuration_value(key: str) -> Optional[str]:
    """
    Get a configuration value by key.

    Args:
        key: Configuration key

    Returns:
        Optional[str]: Configuration value, or None if key doesn't exist

    Raises:
        DatabaseError: If query fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM configuration WHERE key = ?", (key,))
            row = cursor.fetchone()

            if row:
                logger.debug(f"Retrieved configuration value for key: {key}")
                return row['value']
            else:
                logger.debug(f"No configuration value found for key: {key}")
                return None

    except sqlite3.Error as e:
        logger.error(f"Failed to get configuration value: {e}")
        raise DatabaseError(f"Failed to get configuration value: {e}")


def set_configuration_value(key: str, value: str) -> None:
    """
    Set or update a configuration value.

    Args:
        key: Configuration key
        value: Configuration value

    Raises:
        DatabaseError: If operation fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Use UPSERT (INSERT or UPDATE)
            cursor.execute("""
                INSERT INTO configuration (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value))

            conn.commit()
            logger.debug(f"Set configuration value for key: {key}")

    except sqlite3.Error as e:
        logger.error(f"Failed to set configuration value: {e}")
        raise DatabaseError(f"Failed to set configuration value: {e}")


def get_database_stats() -> Dict[str, Any]:
    """
    Get database statistics for monitoring.

    Returns:
        Dict[str, Any]: Database statistics including table counts

    Raises:
        DatabaseError: If query fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get traffic data count
            cursor.execute("SELECT COUNT(*) as count FROM traffic_data")
            traffic_count = cursor.fetchone()['count']

            # Get configuration count
            cursor.execute("SELECT COUNT(*) as count FROM configuration")
            config_count = cursor.fetchone()['count']

            # Get database file size
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

            return {
                'traffic_data_records': traffic_count,
                'configuration_records': config_count,
                'database_size_bytes': db_size,
                'database_path': str(DB_PATH)
            }

    except (sqlite3.Error, OSError) as e:
        logger.error(f"Failed to get database stats: {e}")
        raise DatabaseError(f"Failed to get database stats: {e}")


# Initialize database when module is imported
# Use a flag to track if we've been initialized to avoid duplicate initialization
_initialized = False

def _ensure_initialized():
    """Ensure database is initialized, but only once."""
    global _initialized
    if not _initialized:
        try:
            initialize_database()
            _initialized = True
        except DatabaseError as e:
            logger.error(f"Failed to initialize database on import: {e}")
            # Don't raise the exception during import to allow tests to set their own paths

# Initialize database when module is imported
_ensure_initialized()