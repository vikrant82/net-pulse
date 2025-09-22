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


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.

    Yields:
        sqlite3.Connection: Database connection object

    Raises:
        DatabaseError: If connection fails
    """
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise DatabaseError(f"Failed to connect to database: {e}")
    finally:
        if conn:
            conn.close()


def initialize_database() -> None:
    """
    Initialize the database by creating tables if they don't exist.

    Creates:
        - traffic_data table with network traffic information
        - configuration table for key-value configuration settings

    Raises:
        DatabaseError: If table creation fails
    """
    try:
        with get_db_connection() as conn:
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


def get_aggregated_traffic_data(
    start_time: str,
    data_points: int = 50,
    interface_name: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve aggregated traffic data grouped into exactly N data points.

    This function uses SQL aggregation to efficiently group raw data points
    into the requested number of aggregated points, leveraging database capabilities
    instead of client-side aggregation.

    Args:
        start_time: Start time filter (ISO format string like '1h', '6h', '24h', '7d', '30d')
        data_points: Number of aggregated data points to return (default: 50)
        interface_name: Optional interface name filter
        end_time: Optional end time filter (ISO format)

    Returns:
        List[Dict[str, Any]]: List of aggregated traffic data points

    Raises:
        DatabaseError: If query fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Calculate time window based on start_time parameter
            time_windows = {
                '1h': "datetime('now', '-1 hour')",
                '6h': "datetime('now', '-6 hours')",
                '24h': "datetime('now', '-24 hours')",
                '7d': "datetime('now', '-7 days')",
                '30d': "datetime('now', '-30 days')"
            }

            time_filter = time_windows.get(start_time, "datetime('now', '-24 hours')")

            # Build base query with time and interface filters
            query = """
                WITH ranked_data AS (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (
                            ORDER BY timestamp ASC
                        ) as row_num,
                        COUNT(*) OVER () as total_rows
                    FROM traffic_data
                    WHERE timestamp >= {time_filter}
            """

            params = []

            if interface_name:
                query += " AND interface_name = ?"
                params.append(interface_name)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            query += """
                ),
                bucket_size AS (
                    SELECT
                        CAST(
                            (SELECT COUNT(*) FROM ranked_data) / {data_points}
                            AS INTEGER
                        ) as size
                )
                SELECT
                    AVG(rd.rx_bytes) as avg_rx_bytes,
                    AVG(rd.tx_bytes) as avg_tx_bytes,
                    AVG(rd.rx_packets) as avg_rx_packets,
                    AVG(rd.tx_packets) as avg_tx_packets,
                    rd.interface_name,
                    rd.timestamp as bucket_timestamp
                FROM ranked_data rd
                CROSS JOIN bucket_size bs
                WHERE (rd.row_num - 1) / bs.size < {data_points}
                GROUP BY
                    (rd.row_num - 1) / bs.size,
                    rd.interface_name
                ORDER BY bucket_timestamp ASC
                LIMIT {data_points}
            """

            # Replace placeholders with actual values
            query = query.replace('{time_filter}', time_filter)
            query = query.replace('{data_points}', str(data_points))

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert rows to list of dictionaries
            result = []
            for row in rows:
                result.append({
                    'timestamp': row['bucket_timestamp'],
                    'interface_name': row['interface_name'],
                    'rx_bytes': int(row['avg_rx_bytes']) if row['avg_rx_bytes'] else 0,
                    'tx_bytes': int(row['avg_tx_bytes']) if row['avg_tx_bytes'] else 0,
                    'rx_packets': int(row['avg_rx_packets']) if row['avg_rx_packets'] else 0,
                    'tx_packets': int(row['avg_tx_packets']) if row['avg_tx_packets'] else 0
                })

            logger.info(f"Retrieved {len(result)} aggregated traffic data points for {start_time}")
            return result

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve aggregated traffic data: {e}")
        raise DatabaseError(f"Failed to retrieve aggregated traffic data: {e}")


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
try:
    initialize_database()
except DatabaseError as e:
    logger.error(f"Failed to initialize database on import: {e}")
    raise