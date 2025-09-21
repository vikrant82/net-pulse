#!/usr/bin/env python3
"""
Net-Pulse Collector Module

This module provides continuous network traffic data collection with:
- Background scheduling using APScheduler
- Delta calculation between polling intervals
- Counter rollover handling
- Database storage integration
- Configuration management
- Error handling and resilience
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from contextlib import contextmanager

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.asyncio import AsyncIOExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not available. Install with: pip install apscheduler")

from .database import (
    insert_traffic_data, get_configuration_value, set_configuration_value,
    DatabaseError
)
from .network import (
    get_all_interface_stats, get_interface_stats, validate_interface,
    NetworkError, InterfaceNotFoundError
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CollectionStats:
    """Statistics for data collection operations."""
    total_polls: int = 0
    successful_polls: int = 0
    failed_polls: int = 0
    interfaces_monitored: int = 0
    last_poll_time: Optional[datetime] = None
    last_successful_poll: Optional[datetime] = None
    total_errors: int = 0
    consecutive_failures: int = 0
    start_time: Optional[datetime] = None


@dataclass
class InterfaceData:
    """Stores previous collection data for delta calculation."""
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0
    timestamp: Optional[datetime] = None


class CollectorError(Exception):
    """Custom exception for collector operations."""
    pass


class ConfigurationError(CollectorError):
    """Exception raised for configuration issues."""
    pass


class CollectionError(CollectorError):
    """Exception raised during data collection."""
    pass


class NetworkDataCollector:
    """
    Main orchestrator for continuous network data collection.

    Features:
    - Background scheduling with configurable intervals
    - Delta calculation between polling cycles
    - Automatic counter rollover handling
    - Database storage integration
    - Configuration management
    - Error handling and resilience
    """

    def __init__(self,
                 polling_interval: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the NetworkDataCollector.

        Args:
            polling_interval: Collection interval in seconds (default: 30)
            max_retries: Maximum retry attempts for failed operations
            retry_delay: Delay between retries in seconds
        """
        if not APSCHEDULER_AVAILABLE:
            raise CollectorError(
                "APScheduler is required for NetworkDataCollector. "
                "Install with: pip install apscheduler"
            )

        self.polling_interval = polling_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Collection state
        self._is_running = False
        self._scheduler = None
        self._stop_event = threading.Event()

        # Data storage
        self._previous_data: Dict[str, InterfaceData] = {}
        self._stats = CollectionStats()
        self._lock = threading.Lock()

        # Configuration keys
        self._config_keys = {
            'monitored_interfaces': 'collector.monitored_interfaces',
            'polling_interval': 'collector.polling_interval',
            'max_retries': 'collector.max_retries',
            'retry_delay': 'collector.retry_delay',
            'last_collection': 'collector.last_collection'
        }

        logger.info(f"Initialized NetworkDataCollector with {polling_interval}s interval")

    def start_collection(self) -> None:
        """
        Initialize and start the background collection process.

        Raises:
            CollectorError: If collector is already running or initialization fails
        """
        with self._lock:
            if self._is_running:
                raise CollectorError("Collector is already running")

            try:
                # Initialize scheduler
                self._scheduler = BackgroundScheduler(
                    jobstores={'default': MemoryJobStore()},
                    job_defaults={'coalesce': True, 'max_instances': 1}
                )

                # Add collection job
                self._scheduler.add_job(
                    func=self._collection_job,
                    trigger=IntervalTrigger(seconds=self.polling_interval),
                    id='network_collection',
                    name='Network Data Collection',
                    replace_existing=True
                )

                # Start scheduler
                self._scheduler.start()
                self._is_running = True
                self._stats.start_time = datetime.now()
                self._stop_event.clear()

                logger.info(f"Started network data collection with {self.polling_interval}s interval")

            except Exception as e:
                logger.error(f"Failed to start collection: {e}")
                raise CollectorError(f"Failed to start collection: {e}")

    def stop_collection(self) -> None:
        """
        Gracefully stop the collection process.
        """
        with self._lock:
            if not self._is_running:
                logger.warning("Collector is not running")
                return

            try:
                self._stop_event.set()

                if self._scheduler:
                    self._scheduler.shutdown(wait=True)

                self._is_running = False
                logger.info("Stopped network data collection")

            except Exception as e:
                logger.error(f"Error stopping collection: {e}")
                self._is_running = False

    def collect_once(self) -> Dict[str, Any]:
        """
        Perform a single collection cycle for testing and manual operation.

        Returns:
            Dict[str, Any]: Collection results and statistics

        Raises:
            CollectionError: If collection fails
        """
        try:
            logger.debug("collect_once called")
            result = self._perform_collection()
            logger.debug(f"collect_once got result: {result}")
            collected_count = len(result.get('data', {}))
            logger.debug(f"collect_once calculated interfaces_collected: {collected_count}")
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'interfaces_collected': collected_count,
                'errors': result.get('errors', []),
                'stats': self.get_collection_stats()
            }

        except Exception as e:
            logger.error(f"Single collection cycle failed: {e}")
            raise CollectionError(f"Collection failed: {e}")

    def get_collection_status(self) -> Dict[str, Any]:
        """
        Report current collection status and statistics.

        Returns:
            Dict[str, Any]: Current status and statistics
        """
        with self._lock:
            status = {
                'is_running': self._is_running,
                'stats': {
                    'total_polls': self._stats.total_polls,
                    'successful_polls': self._stats.successful_polls,
                    'failed_polls': self._stats.failed_polls,
                    'interfaces_monitored': self._stats.interfaces_monitored,
                    'last_poll_time': self._stats.last_poll_time.isoformat() if self._stats.last_poll_time else None,
                    'last_successful_poll': self._stats.last_successful_poll.isoformat() if self._stats.last_successful_poll else None,
                    'total_errors': self._stats.total_errors,
                    'consecutive_failures': self._stats.consecutive_failures,
                    'uptime_seconds': (datetime.now() - self._stats.start_time).total_seconds() if self._stats.start_time else 0
                },
                'configuration': self._get_current_config(),
                'previous_data_count': len(self._previous_data)
            }

            return status

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics as a dictionary.

        Returns:
            Dict[str, Any]: Collection statistics
        """
        with self._lock:
            return {
                'total_polls': self._stats.total_polls,
                'successful_polls': self._stats.successful_polls,
                'failed_polls': self._stats.failed_polls,
                'interfaces_monitored': self._stats.interfaces_monitored,
                'last_poll_time': self._stats.last_poll_time.isoformat() if self._stats.last_poll_time else None,
                'last_successful_poll': self._stats.last_successful_poll.isoformat() if self._stats.last_successful_poll else None,
                'total_errors': self._stats.total_errors,
                'consecutive_failures': self._stats.consecutive_failures,
                'uptime_seconds': (datetime.now() - self._stats.start_time).total_seconds() if self._stats.start_time else 0
            }

    def _collection_job(self) -> None:
        """
        Background job for data collection.
        This method is called by the scheduler.
        """
        try:
            result = self._perform_collection()

            # Update statistics
            with self._lock:
                self._stats.total_polls += 1
                self._stats.last_poll_time = datetime.now()

                if result['success']:
                    self._stats.successful_polls += 1
                    self._stats.consecutive_failures = 0
                    self._stats.last_successful_poll = datetime.now()
                else:
                    self._stats.failed_polls += 1
                    self._stats.consecutive_failures += 1
                    self._stats.total_errors += len(result.get('errors', []))

                self._stats.interfaces_monitored = len(self._previous_data)

            # Log collection results
            if result['success']:
                logger.debug(f"Collection cycle completed: {len(result['data'])} interfaces")
            else:
                logger.warning(f"Collection cycle had errors: {result['errors']}")

        except Exception as e:
            logger.error(f"Collection job failed: {e}")
            with self._lock:
                self._stats.total_polls += 1
                self._stats.failed_polls += 1
                self._stats.consecutive_failures += 1
                self._stats.total_errors += 1

    def _perform_collection(self) -> Dict[str, Any]:
        """
        Perform the actual data collection.

        Returns:
            Dict[str, Any]: Collection results with data and any errors
        """
        errors = []
        collected_data = {}

        try:
            # Get monitored interfaces from configuration
            monitored_interfaces = self._get_monitored_interfaces()
            logger.debug(f"Monitored interfaces: {monitored_interfaces}")

            if not monitored_interfaces:
                # If no specific interfaces configured, monitor all available interfaces
                try:
                    all_stats = get_all_interface_stats()
                    monitored_interfaces = list(all_stats.keys())
                    logger.debug(f"No configured interfaces, using all available: {monitored_interfaces}")
                except NetworkError as e:
                    errors.append(f"Failed to get all interface stats: {e}")
                    logger.error(f"Failed to get all interface stats: {e}")
                    return {'success': False, 'data': {}, 'errors': errors}

            # Collect data for each monitored interface
            logger.debug(f"Starting collection for {len(monitored_interfaces)} interfaces")
            for interface_name in monitored_interfaces:
                try:
                    # Get current interface stats
                    current_stats = get_interface_stats(interface_name)
                    logger.debug(f"Got stats for {interface_name}: {current_stats}")

                    # Calculate deltas and handle counter rollover
                    delta_data = self._calculate_deltas(interface_name, current_stats)
                    logger.debug(f"Delta calculation for {interface_name}: {delta_data}")

                    if delta_data:
                        # Store in database
                        self._store_traffic_data(delta_data)
                        logger.debug(f"Stored data for {interface_name}")

                        # Update previous data for next delta calculation
                        self._update_previous_data(interface_name, current_stats)

                        collected_data[interface_name] = delta_data
                        logger.debug(f"Added {interface_name} to collected data")
                    else:
                        # First collection - return current stats as baseline data
                        baseline_data = {
                            'interface_name': interface_name,
                            'timestamp': datetime.now().isoformat(),
                            'rx_bytes': current_stats['rx_bytes'],
                            'tx_bytes': current_stats['tx_bytes'],
                            'rx_packets': current_stats['rx_packets'],
                            'tx_packets': current_stats['tx_packets'],
                            'collection_interval_seconds': 0.0
                        }
                        # Store baseline in database
                        self._store_traffic_data(baseline_data)
                        logger.debug(f"Stored baseline data for {interface_name}")

                        # Update previous data for next delta calculation
                        self._update_previous_data(interface_name, current_stats)

                        collected_data[interface_name] = baseline_data
                        logger.debug(f"Added baseline {interface_name} to collected data")

                except (InterfaceNotFoundError, NetworkError) as e:
                    errors.append(f"Failed to collect data for {interface_name}: {e}")
                    logger.debug(f"Interface error for {interface_name}: {e}")
                except Exception as e:
                    errors.append(f"Unexpected error for {interface_name}: {e}")
                    logger.error(f"Unexpected error collecting data for {interface_name}: {e}")

            logger.debug(f"Collection completed. Collected data: {collected_data}, Errors: {errors}")

            # Update statistics (same as _collection_job)
            with self._lock:
                self._stats.total_polls += 1
                self._stats.last_poll_time = datetime.now()

                if len(errors) == 0:
                    self._stats.successful_polls += 1
                    self._stats.consecutive_failures = 0
                    self._stats.last_successful_poll = datetime.now()
                else:
                    self._stats.failed_polls += 1
                    self._stats.consecutive_failures += 1
                    self._stats.total_errors += len(errors)

                self._stats.interfaces_monitored = len(self._previous_data)

            result = {
                'success': len(errors) == 0,
                'data': collected_data,
                'errors': errors
            }
            logger.debug(f"Returning result: {result}")
            return result

        except Exception as e:
            logger.error(f"Collection cycle failed: {e}")
            return {
                'success': False,
                'data': {},
                'errors': [f"Collection failed: {e}"]
            }

    def _calculate_deltas(self, interface_name: str, current_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate traffic deltas between current and previous collection.

        Args:
            interface_name: Name of the interface
            current_stats: Current interface statistics

        Returns:
            Optional[Dict[str, Any]]: Delta data or None if calculation fails
        """
        try:
            current_time = datetime.now()
            logger.debug(f"Calculating deltas for {interface_name}, current_stats: {current_stats}")

            # Get previous data
            prev_data = self._previous_data.get(interface_name)
            logger.debug(f"Previous data for {interface_name}: {prev_data}")

            if not prev_data:
                # First collection for this interface, store baseline
                logger.debug(f"First collection for {interface_name}, storing baseline")
                self._previous_data[interface_name] = InterfaceData(
                    rx_bytes=current_stats['rx_bytes'],
                    tx_bytes=current_stats['tx_bytes'],
                    rx_packets=current_stats['rx_packets'],
                    tx_packets=current_stats['tx_packets'],
                    timestamp=current_time
                )
                return None

            # Calculate time delta
            if prev_data.timestamp is None:
                logger.warning(f"No previous timestamp for {interface_name}")
                return None

            time_delta = (current_time - prev_data.timestamp).total_seconds()
            if time_delta <= 0:
                logger.warning(f"Invalid time delta for {interface_name}: {time_delta}")
                return None

            # Calculate byte deltas with rollover handling
            rx_bytes_delta = self._calculate_counter_delta(
                prev_data.rx_bytes, current_stats['rx_bytes']
            )
            tx_bytes_delta = self._calculate_counter_delta(
                prev_data.tx_bytes, current_stats['tx_bytes']
            )

            # Calculate packet deltas with rollover handling
            rx_packets_delta = self._calculate_counter_delta(
                prev_data.rx_packets, current_stats['rx_packets']
            )
            tx_packets_delta = self._calculate_counter_delta(
                prev_data.tx_packets, current_stats['tx_packets']
            )

            return {
                'interface_name': interface_name,
                'timestamp': current_time.isoformat(),
                'rx_bytes': rx_bytes_delta,
                'tx_bytes': tx_bytes_delta,
                'rx_packets': rx_packets_delta,
                'tx_packets': tx_packets_delta,
                'collection_interval_seconds': time_delta
            }

        except Exception as e:
            logger.error(f"Failed to calculate deltas for {interface_name}: {e}")
            logger.error(f"Current stats keys: {list(current_stats.keys()) if isinstance(current_stats, dict) else 'Not a dict'}")
            logger.error(f"Current stats: {current_stats}")
            return None

    def _calculate_counter_delta(self, previous: int, current: int) -> int:
        """
        Calculate counter delta with rollover handling.

        Network interface counters can roll over when they reach maximum value.
        This method handles rollover by detecting when current < previous.

        Args:
            previous: Previous counter value
            current: Current counter value

        Returns:
            int: Delta value (always positive)
        """
        if current >= previous:
            return current - previous
        else:
            # Counter rollover detected
            # Assuming 64-bit counters (common for network interfaces)
            # Max value for 64-bit unsigned int is 2^64 - 1
            max_counter_value = 2**64 - 1
            return (max_counter_value - previous) + current

    def _store_traffic_data(self, data: Dict[str, Any]) -> None:
        """
        Store traffic data in the database.

        Args:
            data: Traffic data to store
        """
        try:
            insert_traffic_data(
                timestamp=data['timestamp'],
                interface_name=data['interface_name'],
                rx_bytes=data['rx_bytes'],
                tx_bytes=data['tx_bytes'],
                rx_packets=data['rx_packets'],
                tx_packets=data['tx_packets']
            )
        except DatabaseError as e:
            logger.error(f"Failed to store traffic data: {e}")
            raise

    def _update_previous_data(self, interface_name: str, current_stats: Dict[str, Any]) -> None:
        """
        Update previous data for next delta calculation.

        Args:
            interface_name: Interface name
            current_stats: Current interface statistics
        """
        self._previous_data[interface_name] = InterfaceData(
            rx_bytes=current_stats['rx_bytes'],
            tx_bytes=current_stats['tx_bytes'],
            rx_packets=current_stats['rx_packets'],
            tx_packets=current_stats['tx_packets'],
            timestamp=datetime.now()
        )

    def _get_monitored_interfaces(self) -> List[str]:
        """
        Get list of interfaces to monitor from configuration.

        Returns:
            List[str]: List of interface names to monitor
        """
        try:
            interfaces_str = get_configuration_value(self._config_keys['monitored_interfaces'])
            if interfaces_str:
                interfaces = [iface.strip() for iface in interfaces_str.split(',') if iface.strip()]
                # Validate interfaces exist
                valid_interfaces = []
                for iface in interfaces:
                    if validate_interface(iface):
                        valid_interfaces.append(iface)
                    else:
                        logger.warning(f"Configured interface {iface} not found or not active")
                return valid_interfaces
        except DatabaseError as e:
            logger.error(f"Failed to get monitored interfaces from config: {e}")

        return []

    def _get_current_config(self) -> Dict[str, Any]:
        """
        Get current configuration values.

        Returns:
            Dict[str, Any]: Current configuration
        """
        config = {}
        for key_name, key in self._config_keys.items():
            try:
                value = get_configuration_value(key)
                config[key_name] = value
            except DatabaseError:
                config[key_name] = None
        return config

    @contextmanager
    def _retry_operation(self, operation_name: str):
        """
        Context manager for retrying operations.

        Args:
            operation_name: Name of the operation for logging
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                yield
                return
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"{operation_name} failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries} attempts: {e}")

        raise CollectionError(f"{operation_name} failed: {last_error}")


def initialize_collector_config() -> None:
    """
    Initialize default configuration for the collector.

    This function should be called during application startup.
    """
    config_defaults = {
        'collector.polling_interval': '30',
        'collector.max_retries': '3',
        'collector.retry_delay': '1.0',
        'collector.monitored_interfaces': '',  # Empty means monitor all interfaces
    }

    for key, default_value in config_defaults.items():
        try:
            current_value = get_configuration_value(key)
            if current_value is None:
                set_configuration_value(key, default_value)
                logger.info(f"Set default configuration: {key} = {default_value}")
        except DatabaseError as e:
            logger.error(f"Failed to initialize configuration {key}: {e}")


# Global collector instance
_collector_instance = None
_collector_lock = threading.Lock()


def get_collector() -> NetworkDataCollector:
    """
    Get or create the global collector instance.

    Returns:
        NetworkDataCollector: Global collector instance
    """
    global _collector_instance

    if _collector_instance is None:
        with _collector_lock:
            if _collector_instance is None:
                try:
                    _collector_instance = NetworkDataCollector()
                except CollectorError as e:
                    logger.error(f"Failed to create collector: {e}")
                    raise

    return _collector_instance