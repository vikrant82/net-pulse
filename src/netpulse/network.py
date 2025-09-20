#!/usr/bin/env python3
"""
Net-Pulse Network Module

This module provides network interface discovery and traffic monitoring
functionality using psutil for cross-platform compatibility.

Functions:
    - get_network_interfaces(): Discover available network interfaces
    - get_interface_stats(): Get traffic statistics for a specific interface
    - get_all_interface_stats(): Get traffic statistics for all interfaces
    - validate_interface(): Validate if an interface exists and is active
    - get_primary_interface(): Identify the primary interface based on traffic
"""

import psutil
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Custom exception for network operations."""
    pass


class InterfaceNotFoundError(NetworkError):
    """Exception raised when interface is not found."""
    pass


class PermissionError(NetworkError):
    """Exception raised when there are permission issues."""
    pass


def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
    """
    Discover and return available network interfaces with their details.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of interface names mapped to their details
            including addresses, netmask, broadcast, etc.

    Raises:
        NetworkError: If unable to retrieve network interfaces
    """
    try:
        interfaces = psutil.net_if_addrs()
        logger.debug(f"Discovered {len(interfaces)} network interfaces")

        interface_details = {}
        for interface_name, addresses in interfaces.items():
            interface_info = {
                'name': interface_name,
                'addresses': [],
                'status': 'unknown'
            }

            for addr in addresses:
                addr_info = {
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                }
                interface_info['addresses'].append(addr_info)

            # Try to get interface status
            try:
                stats = psutil.net_if_stats()
                if interface_name in stats:
                    interface_info['status'] = 'up' if stats[interface_name].isup else 'down'
                    interface_info['mtu'] = stats[interface_name].mtu
                    interface_info['speed'] = stats[interface_name].speed
            except Exception as e:
                logger.debug(f"Could not get status for interface {interface_name}: {e}")

            interface_details[interface_name] = interface_info

        return interface_details

    except Exception as e:
        logger.error(f"Failed to get network interfaces: {e}")
        raise NetworkError(f"Failed to discover network interfaces: {e}")


def get_interface_stats(interface_name: str) -> Dict[str, Any]:
    """
    Get current traffic statistics for a specific interface.

    Args:
        interface_name: Name of the network interface (e.g., 'eth0', 'wlan0')

    Returns:
        Dict[str, Any]: Interface statistics including:
            - interface_name: Name of the interface
            - rx_bytes: Received bytes count
            - tx_bytes: Transmitted bytes count
            - rx_packets: Received packets count
            - tx_packets: Transmitted packets count
            - timestamp: Current timestamp

    Raises:
        InterfaceNotFoundError: If interface does not exist
        PermissionError: If permission denied accessing interface stats
        NetworkError: For other network-related errors
    """
    try:
        # Validate interface exists
        if not validate_interface(interface_name):
            raise InterfaceNotFoundError(f"Interface '{interface_name}' not found or not active")

        # Get per-interface statistics
        net_io = psutil.net_io_counters(pernic=True)

        if interface_name not in net_io:
            raise InterfaceNotFoundError(f"Interface '{interface_name}' not found in network statistics")

        stats = net_io[interface_name]

        # Get interface status
        interface_status = 'unknown'
        try:
            all_stats = psutil.net_if_stats()
            if interface_name in all_stats:
                interface_status = 'up' if all_stats[interface_name].isup else 'down'
        except Exception as e:
            logger.debug(f"Could not get interface status for {interface_name}: {e}")

        interface_stats = {
            'interface_name': interface_name,
            'rx_bytes': stats.bytes_recv,
            'tx_bytes': stats.bytes_sent,
            'rx_packets': stats.packets_recv,
            'tx_packets': stats.packets_sent,
            'rx_errors': stats.errin,
            'tx_errors': stats.errout,
            'rx_drops': stats.dropin,
            'tx_drops': stats.dropout,
            'timestamp': datetime.utcnow().isoformat(),
            'status': interface_status
        }

        logger.debug(f"Retrieved stats for interface {interface_name}")
        return interface_stats

    except InterfaceNotFoundError:
        raise
    except PermissionError:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for interface {interface_name}: {e}")
        raise NetworkError(f"Failed to get interface statistics: {e}")


def get_all_interface_stats() -> Dict[str, Dict[str, Any]]:
    """
    Get traffic statistics for all available interfaces.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of interface names mapped to their statistics

    Raises:
        NetworkError: If unable to retrieve network statistics
    """
    try:
        net_io = psutil.net_io_counters(pernic=True)

        if not net_io:
            logger.warning("No network interfaces found")
            return {}

        all_stats = {}
        for interface_name in net_io:
            try:
                stats = get_interface_stats(interface_name)
                all_stats[interface_name] = stats
            except (InterfaceNotFoundError, NetworkError) as e:
                logger.debug(f"Skipping interface {interface_name}: {e}")
                continue

        logger.debug(f"Retrieved stats for {len(all_stats)} interfaces")
        return all_stats

    except Exception as e:
        logger.error(f"Failed to get all interface stats: {e}")
        raise NetworkError(f"Failed to get all interface statistics: {e}")


def validate_interface(interface_name: str) -> bool:
    """
    Validate if a network interface exists and is active.

    Args:
        interface_name: Name of the network interface to validate

    Returns:
        bool: True if interface exists and is active, False otherwise
    """
    try:
        # Check if interface exists in addresses
        interfaces = psutil.net_if_addrs()
        if interface_name not in interfaces:
            return False

        # Check if interface is up
        try:
            stats = psutil.net_if_stats()
            if interface_name in stats:
                return stats[interface_name].isup
        except Exception:
            # If we can't get status, assume it's valid if it has addresses
            return len(interfaces[interface_name]) > 0

        return False

    except Exception as e:
        logger.debug(f"Error validating interface {interface_name}: {e}")
        return False


def get_primary_interface() -> Optional[str]:
    """
    Identify the primary network interface based on traffic activity.

    The primary interface is determined by:
    1. Interface must be active (up)
    2. Interface must have traffic (bytes sent/received > 0)
    3. Prefer interfaces with highest traffic volume

    Returns:
        Optional[str]: Name of the primary interface, or None if no suitable interface found

    Raises:
        NetworkError: If unable to determine primary interface
    """
    try:
        all_stats = get_all_interface_stats()

        if not all_stats:
            logger.warning("No active interfaces found")
            return None

        # Filter for active interfaces with traffic
        active_interfaces = []
        for interface_name, stats in all_stats.items():
            if (stats['status'] == 'up' and
                (stats['rx_bytes'] > 0 or stats['tx_bytes'] > 0)):
                active_interfaces.append((interface_name, stats))

        if not active_interfaces:
            logger.warning("No interfaces with traffic found")
            return None

        # Sort by total traffic (rx + tx bytes) and return the highest
        active_interfaces.sort(key=lambda x: x[1]['rx_bytes'] + x[1]['tx_bytes'], reverse=True)
        primary_interface = active_interfaces[0][0]

        logger.debug(f"Identified primary interface: {primary_interface}")
        return primary_interface

    except Exception as e:
        logger.error(f"Failed to determine primary interface: {e}")
        raise NetworkError(f"Failed to determine primary interface: {e}")


def get_interface_traffic_summary() -> Dict[str, Any]:
    """
    Get a summary of all network traffic across all interfaces.

    Returns:
        Dict[str, Any]: Summary including total bytes/packets sent and received
    """
    try:
        all_stats = get_all_interface_stats()

        summary = {
            'total_interfaces': len(all_stats),
            'active_interfaces': sum(1 for stats in all_stats.values() if stats['status'] == 'up'),
            'total_rx_bytes': 0,
            'total_tx_bytes': 0,
            'total_rx_packets': 0,
            'total_tx_packets': 0,
            'timestamp': datetime.utcnow().isoformat()
        }

        for stats in all_stats.values():
            summary['total_rx_bytes'] += stats['rx_bytes']
            summary['total_tx_bytes'] += stats['tx_bytes']
            summary['total_rx_packets'] += stats['rx_packets']
            summary['total_tx_packets'] += stats['tx_packets']

        return summary

    except Exception as e:
        logger.error(f"Failed to get traffic summary: {e}")
        raise NetworkError(f"Failed to get traffic summary: {e}")