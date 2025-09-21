#!/usr/bin/env python3
"""
Net-Pulse Auto-Detection Module

This module provides intelligent network interface discovery and primary interface
identification for automatic system configuration. It analyzes traffic patterns,
identifies active interfaces, and populates initial configuration settings.

Core Components:
    - InterfaceAnalyzer: Main orchestrator for interface analysis
    - discover_interfaces(): Enhanced interface discovery with filtering
    - identify_primary_interface(): Traffic-based primary interface detection
    - analyze_interface_activity(): Real-time traffic monitoring and analysis
    - populate_initial_config(): Database configuration population

The module integrates with existing network and database modules to provide
seamless auto-configuration for most common network setups.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone

from . import network
from . import database

# Configure logging
logger = logging.getLogger(__name__)


class AutoDetectionError(Exception):
    """Custom exception for auto-detection operations."""
    pass


class InterfaceAnalyzer:
    """
    Main orchestrator for network interface analysis and auto-detection.

    This class provides comprehensive interface discovery, analysis, and
    configuration management for automatic system setup.
    """

    def __init__(self):
        """Initialize the InterfaceAnalyzer."""
        self.network_module = network
        self.database_module = database
        self._traffic_samples = []
        self._monitoring_duration = 10  # seconds
        self._sample_interval = 1  # seconds

    def discover_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover and analyze available network interfaces.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of interface names mapped to their details

        Raises:
            AutoDetectionError: If interface discovery fails
        """
        try:
            logger.info("Starting interface discovery process")

            # Get interfaces from network module
            interfaces = self.network_module.get_network_interfaces()

            if not interfaces:
                logger.warning("No network interfaces discovered")
                return {}

            # Filter and enhance interface information
            filtered_interfaces = {}
            for interface_name, details in interfaces.items():
                if self._is_valid_interface(interface_name, details):
                    enhanced_details = self._enhance_interface_details(interface_name, details)
                    filtered_interfaces[interface_name] = enhanced_details
                    logger.debug(f"Discovered valid interface: {interface_name}")

            logger.info(f"Discovered {len(filtered_interfaces)} valid interfaces")
            return filtered_interfaces

        except Exception as e:
            logger.error(f"Interface discovery failed: {e}")
            raise AutoDetectionError(f"Failed to discover interfaces: {e}")

    def identify_primary_interface(self, monitoring_duration: int = 10) -> Optional[str]:
        """
        Identify the primary network interface based on traffic patterns.

        Args:
            monitoring_duration: Duration in seconds to monitor traffic (default: 10)

        Returns:
            Optional[str]: Name of the primary interface, or None if not found

        Raises:
            AutoDetectionError: If primary interface identification fails
        """
        try:
            logger.info(f"Starting primary interface identification (monitoring for {monitoring_duration}s)")

            interfaces = self.discover_interfaces()
            if not interfaces:
                logger.warning("No interfaces available for primary interface detection")
                return None

            # Monitor traffic patterns
            traffic_data = self._monitor_traffic_patterns(list(interfaces.keys()), monitoring_duration)

            if not traffic_data:
                logger.warning("No traffic data collected during monitoring period")
                return None

            # Analyze traffic patterns to identify primary interface
            primary_interface = self._analyze_traffic_for_primary_interface(traffic_data)

            if primary_interface:
                logger.info(f"Identified primary interface: {primary_interface}")
                return primary_interface
            else:
                logger.warning("Could not determine primary interface from traffic analysis")
                return None

        except Exception as e:
            logger.error(f"Primary interface identification failed: {e}")
            raise AutoDetectionError(f"Failed to identify primary interface: {e}")

    def analyze_interface_activity(self, interface_name: str, duration: int = 5) -> Dict[str, Any]:
        """
        Analyze traffic activity for a specific interface over time.

        Args:
            interface_name: Name of the interface to analyze
            duration: Analysis duration in seconds (default: 5)

        Returns:
            Dict[str, Any]: Activity analysis results

        Raises:
            AutoDetectionError: If activity analysis fails
        """
        try:
            logger.info(f"Analyzing activity for interface {interface_name} ({duration}s)")

            # Validate interface
            if not self.network_module.validate_interface(interface_name):
                raise AutoDetectionError(f"Interface {interface_name} is not valid or active")

            # Collect traffic samples
            samples = []
            start_time = time.time()

            while time.time() - start_time < duration:
                try:
                    stats = self.network_module.get_interface_stats(interface_name)
                    samples.append({
                        'timestamp': stats['timestamp'],
                        'rx_bytes': stats['rx_bytes'],
                        'tx_bytes': stats['tx_bytes'],
                        'rx_packets': stats['rx_packets'],
                        'tx_packets': stats['tx_packets']
                    })
                    time.sleep(1)  # Sample every second
                except Exception as e:
                    logger.debug(f"Failed to get stats during analysis: {e}")
                    continue

            if not samples:
                return {
                    'interface_name': interface_name,
                    'activity_level': 'inactive',
                    'total_samples': 0,
                    'analysis_duration': duration
                }

            # Calculate activity metrics
            initial_stats = samples[0]
            final_stats = samples[-1]

            rx_rate = (final_stats['rx_bytes'] - initial_stats['rx_bytes']) / duration
            tx_rate = (final_stats['tx_bytes'] - initial_stats['tx_bytes']) / duration
            rx_packet_rate = (final_stats['rx_packets'] - initial_stats['rx_packets']) / duration
            tx_packet_rate = (final_stats['tx_packets'] - initial_stats['tx_packets']) / duration

            # Determine activity level
            total_rate = rx_rate + tx_rate
            if total_rate > 1000000:  # > 1 MB/s
                activity_level = 'high'
            elif total_rate > 100000:  # > 100 KB/s
                activity_level = 'medium'
            elif total_rate > 1000:  # > 1 KB/s
                activity_level = 'low'
            else:
                activity_level = 'minimal'

            analysis_result = {
                'interface_name': interface_name,
                'activity_level': activity_level,
                'rx_bytes_per_second': rx_rate,
                'tx_bytes_per_second': tx_rate,
                'rx_packets_per_second': rx_packet_rate,
                'tx_packets_per_second': tx_packet_rate,
                'total_samples': len(samples),
                'analysis_duration': duration,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            logger.debug(f"Activity analysis completed for {interface_name}: {activity_level}")
            return analysis_result

        except Exception as e:
            logger.error(f"Activity analysis failed for interface {interface_name}: {e}")
            raise AutoDetectionError(f"Failed to analyze interface activity: {e}")

    def populate_initial_config(self) -> Dict[str, Any]:
        """
        Populate initial configuration with auto-detected interface settings.

        Returns:
            Dict[str, Any]: Configuration summary of what was set

        Raises:
            AutoDetectionError: If configuration population fails
        """
        try:
            logger.info("Starting initial configuration population")

            # Discover interfaces
            interfaces = self.discover_interfaces()
            if not interfaces:
                logger.warning("No interfaces to configure")
                return {'status': 'no_interfaces', 'configured_interfaces': 0}

            # Identify primary interface
            primary_interface = self.identify_primary_interface()

            # Store interface configuration
            config_summary = {
                'status': 'success',
                'configured_interfaces': 0,
                'primary_interface': primary_interface,
                'interface_details': {}
            }

            for interface_name, details in interfaces.items():
                # Store interface details
                config_key = f"interface.{interface_name}"
                config_value = self._serialize_interface_config(details)

                try:
                    self.database_module.set_configuration_value(config_key, config_value)
                    config_summary['interface_details'][interface_name] = 'configured'
                    config_summary['configured_interfaces'] += 1
                    logger.debug(f"Configured interface: {interface_name}")
                except Exception as e:
                    logger.error(f"Failed to configure interface {interface_name}: {e}")
                    config_summary['interface_details'][interface_name] = f'error: {e}'

            # Set primary interface configuration
            if primary_interface:
                try:
                    self.database_module.set_configuration_value('primary_interface', primary_interface)
                    logger.info(f"Set primary interface: {primary_interface}")
                except Exception as e:
                    logger.error(f"Failed to set primary interface: {e}")
                    config_summary['primary_interface_error'] = str(e)

            # Set auto-detection completion flag
            try:
                self.database_module.set_configuration_value('auto_detection_completed', 'true')
                self.database_module.set_configuration_value('auto_detection_timestamp', datetime.now(timezone.utc).isoformat())
            except Exception as e:
                logger.error(f"Failed to set auto-detection completion flag: {e}")

            logger.info(f"Configuration population completed: {config_summary['configured_interfaces']} interfaces configured")
            return config_summary

        except Exception as e:
            logger.error(f"Configuration population failed: {e}")
            raise AutoDetectionError(f"Failed to populate initial configuration: {e}")

    def _is_valid_interface(self, interface_name: str, details: Dict[str, Any]) -> bool:
        """
        Determine if an interface is valid for auto-detection.

        Args:
            interface_name: Name of the interface
            details: Interface details dictionary

        Returns:
            bool: True if interface is valid, False otherwise
        """
        # Skip loopback interfaces
        if interface_name in ['lo', 'lo0', 'loopback']:
            return False

        # Skip docker interfaces
        if interface_name.startswith(('docker', 'veth', 'br-')):
            return False

        # Skip interfaces without addresses (except wireless)
        if not details.get('addresses') and not interface_name.startswith('wlan'):
            return False

        # Skip interfaces that are down
        if details.get('status') == 'down':
            return False

        return True

    def _enhance_interface_details(self, interface_name: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance interface details with additional analysis.

        Args:
            interface_name: Name of the interface
            details: Basic interface details

        Returns:
            Dict[str, Any]: Enhanced interface details
        """
        enhanced = details.copy()

        # Add interface type classification
        if interface_name.startswith('wlan'):
            enhanced['type'] = 'wireless'
        elif interface_name.startswith('eth'):
            enhanced['type'] = 'ethernet'
        elif interface_name.startswith('en'):
            enhanced['type'] = 'ethernet'
        elif interface_name.startswith('wlp'):
            enhanced['type'] = 'wireless'
        else:
            enhanced['type'] = 'unknown'

        # Add activity assessment
        try:
            activity = self.analyze_interface_activity(interface_name, duration=2)
            enhanced['activity_analysis'] = activity
        except Exception as e:
            logger.debug(f"Could not analyze activity for {interface_name}: {e}")
            enhanced['activity_analysis'] = None

        return enhanced

    def _monitor_traffic_patterns(self, interface_names: List[str], duration: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Monitor traffic patterns for multiple interfaces over time.

        Args:
            interface_names: List of interface names to monitor
            duration: Monitoring duration in seconds

        Returns:
            Dict[str, List[Dict[str, Any]]]: Traffic data for each interface
        """
        logger.debug(f"Monitoring traffic for {len(interface_names)} interfaces over {duration}s")

        traffic_data = {name: [] for name in interface_names}
        start_time = time.time()

        while time.time() - start_time < duration:
            for interface_name in interface_names:
                try:
                    stats = self.network_module.get_interface_stats(interface_name)
                    traffic_data[interface_name].append({
                        'timestamp': stats['timestamp'],
                        'rx_bytes': stats['rx_bytes'],
                        'tx_bytes': stats['tx_bytes'],
                        'rx_packets': stats['rx_packets'],
                        'tx_packets': stats['tx_packets']
                    })
                except Exception as e:
                    logger.debug(f"Failed to get stats for {interface_name} during monitoring: {e}")

            time.sleep(self._sample_interval)

        logger.debug(f"Collected traffic data: { {k: len(v) for k, v in traffic_data.items()} } samples")
        return traffic_data

    def _analyze_traffic_for_primary_interface(self, traffic_data: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        """
        Analyze traffic data to identify the primary interface.

        Args:
            traffic_data: Traffic data for each interface

        Returns:
            Optional[str]: Name of the primary interface, or None
        """
        if not traffic_data:
            return None

        # Calculate total traffic for each interface
        interface_scores = {}

        for interface_name, samples in traffic_data.items():
            if not samples:
                continue

            # Calculate total bytes transferred
            initial = samples[0]
            final = samples[-1]

            total_bytes = (final['rx_bytes'] - initial['rx_bytes'] +
                          final['tx_bytes'] - initial['tx_bytes'])

            # Calculate packets per second
            duration = len(samples) - 1  # Number of intervals
            if duration > 0:
                packets_per_second = (final['rx_packets'] - initial['rx_packets'] +
                                    final['tx_packets'] - initial['tx_packets']) / duration
            else:
                packets_per_second = 0

            # Score combines total traffic and packet rate
            score = total_bytes + (packets_per_second * 1000)  # Weight packet rate
            interface_scores[interface_name] = score

        if not interface_scores:
            return None

        # Return interface with highest score
        primary_interface = max(interface_scores.items(), key=lambda x: x[1])[0]

        # Only return if there's significant traffic
        if interface_scores[primary_interface] > 1000:  # At least 1KB of traffic
            return primary_interface
        else:
            return None

    def _serialize_interface_config(self, details: Dict[str, Any]) -> str:
        """
        Serialize interface details to a configuration string.

        Args:
            details: Interface details dictionary

        Returns:
            str: Serialized configuration string
        """
        # Create a simplified representation for storage
        config_parts = []

        if 'type' in details:
            config_parts.append(f"type:{details['type']}")

        if 'status' in details:
            config_parts.append(f"status:{details['status']}")

        if 'mtu' in details:
            config_parts.append(f"mtu:{details['mtu']}")

        if 'speed' in details and details['speed']:
            config_parts.append(f"speed:{details['speed']}")

        # Add addresses
        addresses = details.get('addresses', [])
        if addresses:
            addr_strs = []
            for addr in addresses:
                if addr.get('address'):
                    addr_strs.append(addr['address'])
            if addr_strs:
                config_parts.append(f"addresses:{','.join(addr_strs)}")

        return '|'.join(config_parts)


def initialize_auto_detection() -> Dict[str, Any]:
    """
    Initialize auto-detection and populate initial configuration.

    This function should be called during application startup to perform
    initial interface discovery and configuration.

    Returns:
        Dict[str, Any]: Auto-detection results and status

    Raises:
        AutoDetectionError: If initialization fails
    """
    try:
        logger.info("Starting auto-detection initialization")

        # Check if already initialized
        if database.get_configuration_value('auto_detection_completed') == 'true':
            logger.info("Auto-detection already completed, skipping initialization")
            return {
                'status': 'already_initialized',
                'message': 'Auto-detection was already performed'
            }

        # Create analyzer and run detection
        analyzer = InterfaceAnalyzer()
        config_result = analyzer.populate_initial_config()

        logger.info("Auto-detection initialization completed successfully")
        return {
            'status': 'success',
            'message': 'Auto-detection completed successfully',
            'details': config_result
        }

    except Exception as e:
        logger.error(f"Auto-detection initialization failed: {e}")
        raise AutoDetectionError(f"Auto-detection initialization failed: {e}")


def get_detected_interfaces() -> Dict[str, Dict[str, Any]]:
    """
    Get interfaces that were auto-detected and stored in configuration.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of detected interfaces and their details
    """
    try:
        # Get all configuration keys that start with 'interface.'
        interfaces = {}

        # This would need to be implemented based on how we query configuration keys
        # For now, we'll return a placeholder implementation
        logger.debug("Retrieving detected interfaces from configuration")
        return interfaces

    except Exception as e:
        logger.error(f"Failed to get detected interfaces: {e}")
        raise AutoDetectionError(f"Failed to get detected interfaces: {e}")


def reset_auto_detection() -> Dict[str, Any]:
    """
    Reset auto-detection configuration and allow re-detection.

    Returns:
        Dict[str, Any]: Reset operation results
    """
    try:
        logger.info("Resetting auto-detection configuration")

        # Remove auto-detection completion flag
        try:
            database.set_configuration_value('auto_detection_completed', 'false')
        except Exception as e:
            logger.debug(f"Could not reset completion flag: {e}")

        # Remove primary interface setting
        try:
            database.set_configuration_value('primary_interface', '')
        except Exception as e:
            logger.debug(f"Could not reset primary interface: {e}")

        logger.info("Auto-detection reset completed")
        return {
            'status': 'success',
            'message': 'Auto-detection configuration reset'
        }

    except Exception as e:
        logger.error(f"Auto-detection reset failed: {e}")
        raise AutoDetectionError(f"Auto-detection reset failed: {e}")