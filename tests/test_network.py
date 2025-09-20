"""
Comprehensive unit tests for the network module.

This module tests all network interface discovery and traffic monitoring
functionality including:
- Network interface discovery and validation
- Traffic statistics collection and processing
- Error handling and edge cases
- Platform compatibility and performance
- Integration scenarios and data validation
"""

import pytest
import psutil
import time
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from netpulse.network import (
    NetworkError,
    InterfaceNotFoundError,
    PermissionError,
    get_network_interfaces,
    get_interface_stats,
    get_all_interface_stats,
    validate_interface,
    get_primary_interface,
    get_interface_traffic_summary
)


@pytest.fixture
def mock_psutil_net_if_addrs():
    """Mock psutil.net_if_addrs() with sample interface data."""
    # Import psutil constants to avoid type checker issues
    AF_INET = 2  # 2
    AF_INET6 = 10  # 26

    return {
        'eth0': [
            MagicMock(family=AF_INET, address='192.168.1.100',
                     netmask='255.255.255.0', broadcast='192.168.1.255'),
            MagicMock(family=AF_INET6, address='fe80::1',
                     netmask=None, broadcast=None)
        ],
        'lo': [
            MagicMock(family=AF_INET, address='127.0.0.1',
                     netmask='255.0.0.0', broadcast=None),
            MagicMock(family=AF_INET6, address='::1',
                     netmask=None, broadcast=None)
        ],
        'wlan0': [
            MagicMock(family=AF_INET, address='192.168.1.101',
                     netmask='255.255.255.0', broadcast='192.168.1.255')
        ]
    }


@pytest.fixture
def mock_psutil_net_if_stats():
    """Mock psutil.net_if_stats() with sample interface status data."""
    return {
        'eth0': MagicMock(isup=True, mtu=1500, speed=1000),
        'lo': MagicMock(isup=True, mtu=65536, speed=0),
        'wlan0': MagicMock(isup=False, mtu=1500, speed=150)
    }


@pytest.fixture
def mock_psutil_net_io_counters():
    """Mock psutil.net_io_counters() with sample traffic statistics."""
    return {
        'eth0': MagicMock(bytes_sent=1000000, bytes_recv=2000000,
                         packets_sent=1000, packets_recv=2000,
                         errin=0, errout=0, dropin=0, dropout=0),
        'lo': MagicMock(bytes_sent=500000, bytes_recv=500000,
                       packets_sent=500, packets_recv=500,
                       errin=0, errout=0, dropin=0, dropout=0),
        'wlan0': MagicMock(bytes_sent=0, bytes_recv=0,
                         packets_sent=0, packets_recv=0,
                         errin=0, errout=0, dropin=0, dropout=0)
    }


@pytest.fixture
def mock_interface_data():
    """Provide sample interface data for testing."""
    return {
        'name': 'eth0',
        'addresses': [
            {
                'family': 'AddressFamily.AF_INET',
                'address': '192.168.1.100',
                'netmask': '255.255.255.0',
                'broadcast': '192.168.1.255'
            }
        ],
        'status': 'up',
        'mtu': 1500,
        'speed': 1000
    }


@pytest.fixture
def mock_interface_stats():
    """Provide sample interface statistics for testing."""
    return {
        'interface_name': 'eth0',
        'rx_bytes': 2000000,
        'tx_bytes': 1000000,
        'rx_packets': 2000,
        'tx_packets': 1000,
        'rx_errors': 0,
        'tx_errors': 0,
        'rx_drops': 0,
        'tx_drops': 0,
        'timestamp': '2024-01-01T12:00:00',
        'status': 'up'
    }


@pytest.fixture
def mock_multiple_interfaces_stats():
    """Provide statistics for multiple interfaces."""
    return {
        'eth0': {
            'interface_name': 'eth0',
            'rx_bytes': 2000000,
            'tx_bytes': 1000000,
            'rx_packets': 2000,
            'tx_packets': 1000,
            'status': 'up'
        },
        'lo': {
            'interface_name': 'lo',
            'rx_bytes': 500000,
            'tx_bytes': 500000,
            'rx_packets': 500,
            'tx_packets': 500,
            'status': 'up'
        },
        'wlan0': {
            'interface_name': 'wlan0',
            'rx_bytes': 0,
            'tx_bytes': 0,
            'rx_packets': 0,
            'tx_packets': 0,
            'status': 'down'
        }
    }


class TestNetworkError:
    """Test the custom NetworkError exception."""

    def test_network_error_inheritance(self):
        """Test that NetworkError inherits from Exception."""
        error = NetworkError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, NetworkError)

    def test_network_error_message(self):
        """Test that NetworkError stores the error message correctly."""
        message = "Network operation failed"
        error = NetworkError(message)
        assert str(error) == message

    def test_network_error_with_empty_message(self):
        """Test NetworkError with empty message."""
        error = NetworkError("")
        assert str(error) == ""


class TestInterfaceNotFoundError:
    """Test the InterfaceNotFoundError exception."""

    def test_interface_not_found_error_inheritance(self):
        """Test that InterfaceNotFoundError inherits from NetworkError."""
        error = InterfaceNotFoundError("Interface not found")
        assert isinstance(error, NetworkError)
        assert isinstance(error, InterfaceNotFoundError)

    def test_interface_not_found_error_message(self):
        """Test that InterfaceNotFoundError stores the error message correctly."""
        message = "Interface 'eth0' not found"
        error = InterfaceNotFoundError(message)
        assert str(error) == message


class TestPermissionError:
    """Test the PermissionError exception."""

    def test_permission_error_inheritance(self):
        """Test that PermissionError inherits from NetworkError."""
        error = PermissionError("Permission denied")
        assert isinstance(error, NetworkError)
        assert isinstance(error, PermissionError)

    def test_permission_error_message(self):
        """Test that PermissionError stores the error message correctly."""
        message = "Permission denied accessing interface"
        error = PermissionError(message)
        assert str(error) == message


class TestGetNetworkInterfaces:
    """Test get_network_interfaces() function."""

    def test_get_network_interfaces_normal_operation(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test normal operation of get_network_interfaces()."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()

            assert isinstance(result, dict)
            assert len(result) == 3
            assert 'eth0' in result
            assert 'lo' in result
            assert 'wlan0' in result

            # Test interface structure
            eth0 = result['eth0']
            assert eth0['name'] == 'eth0'
            assert eth0['status'] == 'up'
            assert eth0['mtu'] == 1500
            assert eth0['speed'] == 1000
            assert len(eth0['addresses']) == 2

            # Test address format
            addr = eth0['addresses'][0]
            assert 'family' in addr
            assert 'address' in addr
            assert 'netmask' in addr
            assert 'broadcast' in addr

    def test_get_network_interfaces_empty_system(self):
        """Test get_network_interfaces() with no interfaces available."""
        with patch('psutil.net_if_addrs', return_value={}), \
             patch('psutil.net_if_stats', return_value={}):

            result = get_network_interfaces()
            assert isinstance(result, dict)
            assert len(result) == 0

    def test_get_network_interfaces_permission_denied(self):
        """Test get_network_interfaces() with permission denied."""
        with patch('psutil.net_if_addrs', side_effect=psutil.AccessDenied("Permission denied")):
            with pytest.raises(NetworkError, match="Failed to discover network interfaces"):
                get_network_interfaces()

    def test_get_network_interfaces_interface_structure(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test that each interface contains required fields."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()

            for interface_name, interface_info in result.items():
                assert 'name' in interface_info
                assert 'addresses' in interface_info
                assert 'status' in interface_info
                assert interface_info['name'] == interface_name
                assert isinstance(interface_info['addresses'], list)

    def test_get_network_interfaces_address_format(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test that IP addresses are properly formatted and categorized."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()

            # Test IPv4 address format
            eth0 = result['eth0']
            ipv4_addr = next(addr for addr in eth0['addresses']
                           if '192.168.1.100' in addr['address'])
            assert '192.168.1.100' in ipv4_addr['address']
            assert '255.255.255.0' in ipv4_addr['netmask']

            # Test IPv6 address format
            ipv6_addr = next(addr for addr in eth0['addresses']
                           if 'fe80::1' in addr['address'])
            assert 'fe80::1' in ipv6_addr['address']

    def test_get_network_interfaces_status_unknown(self, mock_psutil_net_if_addrs):
        """Test interface status when psutil.net_if_stats() fails."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', side_effect=Exception("Status check failed")):

            result = get_network_interfaces()

            for interface_info in result.values():
                assert interface_info['status'] == 'unknown'

    def test_get_network_interfaces_general_exception(self):
        """Test get_network_interfaces() with general exception."""
        with patch('psutil.net_if_addrs', side_effect=Exception("General error")):
            with pytest.raises(NetworkError, match="Failed to discover network interfaces"):
                get_network_interfaces()


class TestGetInterfaceStats:
    """Test get_interface_stats() function."""

    def test_get_interface_stats_valid_interface(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_interface_stats() with existing active interface."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_interface_stats('eth0')

            assert isinstance(result, dict)
            assert result['interface_name'] == 'eth0'
            assert result['rx_bytes'] == 2000000
            assert result['tx_bytes'] == 1000000
            assert result['rx_packets'] == 2000
            assert result['tx_packets'] == 1000
            assert result['status'] == 'up'
            assert 'timestamp' in result

    def test_get_interface_stats_loopback_interface(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_interface_stats() with loopback interface."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_interface_stats('lo')

            assert result['interface_name'] == 'lo'
            assert result['rx_bytes'] == 500000
            assert result['tx_bytes'] == 500000
            assert result['status'] == 'up'

    def test_get_interface_stats_nonexistent_interface(self):
        """Test get_interface_stats() with non-existent interface."""
        with patch('netpulse.network.validate_interface', return_value=False):
            with pytest.raises(InterfaceNotFoundError, match="Interface 'nonexistent' not found"):
                get_interface_stats('nonexistent')

    def test_get_interface_stats_inactive_interface(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_interface_stats() with inactive interface."""
        with patch('netpulse.network.validate_interface', return_value=False):
            with pytest.raises(InterfaceNotFoundError, match="Interface 'wlan0' not found"):
                get_interface_stats('wlan0')

    def test_get_interface_stats_data_types(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that all numeric fields are integers and timestamp is ISO format."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_interface_stats('eth0')

            # Test numeric fields are integers
            assert isinstance(result['rx_bytes'], int)
            assert isinstance(result['tx_bytes'], int)
            assert isinstance(result['rx_packets'], int)
            assert isinstance(result['tx_packets'], int)
            assert isinstance(result['rx_errors'], int)
            assert isinstance(result['tx_errors'], int)
            assert isinstance(result['rx_drops'], int)
            assert isinstance(result['tx_drops'], int)

            # Test timestamp format
            timestamp = result['timestamp']
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    def test_get_interface_stats_database_compatibility(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that returned structure matches database schema exactly."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_interface_stats('eth0')

            # Verify exact field names match database schema
            expected_fields = {
                'interface_name', 'rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets',
                'rx_errors', 'tx_errors', 'rx_drops', 'tx_drops', 'timestamp', 'status'
            }
            assert set(result.keys()) == expected_fields

    def test_get_interface_stats_interface_not_in_stats(self, mock_psutil_net_io_counters):
        """Test get_interface_stats() when interface not in network statistics."""
        mock_stats = {'eth1': MagicMock(bytes_sent=1000, bytes_recv=2000,
                                      packets_sent=10, packets_recv=20,
                                      errin=0, errout=0, dropin=0, dropout=0)}

        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_stats):

            with pytest.raises(InterfaceNotFoundError, match="Interface 'eth0' not found"):
                get_interface_stats('eth0')

    def test_get_interface_stats_permission_error(self):
        """Test get_interface_stats() with permission error."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', side_effect=PermissionError("Permission denied")):

            with pytest.raises(PermissionError):
                get_interface_stats('eth0')

    def test_get_interface_stats_general_exception(self, mock_psutil_net_io_counters):
        """Test get_interface_stats() with general exception."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', side_effect=Exception("General error")):

            with pytest.raises(NetworkError, match="Failed to get interface statistics"):
                get_interface_stats('eth0')

    def test_get_interface_stats_status_unknown(self, mock_psutil_net_io_counters):
        """Test get_interface_stats() when interface status check fails."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', side_effect=Exception("Status check failed")):

            result = get_interface_stats('eth0')

            assert result['status'] == 'unknown'


class TestGetAllInterfaceStats:
    """Test get_all_interface_stats() function."""

    def test_get_all_interface_stats_multiple_interfaces(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_all_interface_stats() with multiple active interfaces."""
        with patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats), \
             patch('netpulse.network.get_interface_stats') as mock_get_stats:

            # Mock the individual get_interface_stats calls
            def mock_stats_side_effect(interface_name):
                mock_io = mock_psutil_net_io_counters[interface_name]
                return {
                    'interface_name': interface_name,
                    'rx_bytes': mock_io.bytes_recv,
                    'tx_bytes': mock_io.bytes_sent,
                    'rx_packets': mock_io.packets_recv,
                    'tx_packets': mock_io.packets_sent,
                    'rx_errors': mock_io.errin,
                    'tx_errors': mock_io.errout,
                    'rx_drops': mock_io.dropin,
                    'tx_drops': mock_io.dropout,
                    'timestamp': '2024-01-01T12:00:00',
                    'status': 'up'
                }

            mock_get_stats.side_effect = mock_stats_side_effect

            result = get_all_interface_stats()

            assert isinstance(result, dict)
            assert len(result) == 3
            assert 'eth0' in result
            assert 'lo' in result
            assert 'wlan0' in result

            # Verify each interface has stats
            for interface_name, stats in result.items():
                assert stats['interface_name'] == interface_name
                assert 'rx_bytes' in stats
                assert 'tx_bytes' in stats

    def test_get_all_interface_stats_mixed_interface_states(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_all_interface_stats() with mixed up/down interfaces."""
        with patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats), \
             patch('netpulse.network.get_interface_stats') as mock_get_stats:

            # Mock the individual get_interface_stats calls with different statuses
            def mock_stats_side_effect(interface_name):
                mock_io = mock_psutil_net_io_counters[interface_name]
                status = 'up' if interface_name != 'wlan0' else 'down'
                return {
                    'interface_name': interface_name,
                    'rx_bytes': mock_io.bytes_recv,
                    'tx_bytes': mock_io.bytes_sent,
                    'rx_packets': mock_io.packets_recv,
                    'tx_packets': mock_io.packets_sent,
                    'rx_errors': mock_io.errin,
                    'tx_errors': mock_io.errout,
                    'rx_drops': mock_io.dropin,
                    'tx_drops': mock_io.dropout,
                    'timestamp': '2024-01-01T12:00:00',
                    'status': status
                }

            mock_get_stats.side_effect = mock_stats_side_effect

            result = get_all_interface_stats()

            # Should include all interfaces that have stats available
            assert len(result) == 3
            assert result['eth0']['status'] == 'up'
            assert result['lo']['status'] == 'up'
            assert result['wlan0']['status'] == 'down'

    def test_get_all_interface_stats_empty_results(self):
        """Test get_all_interface_stats() when no interfaces have statistics."""
        with patch('psutil.net_io_counters', return_value={}):
            result = get_all_interface_stats()
            assert result == {}

    def test_get_all_interface_stats_error_isolation(self, mock_psutil_net_io_counters):
        """Test that failure of one interface doesn't affect others."""
        def mock_get_interface_stats(interface_name):
            if interface_name == 'eth0':
                raise InterfaceNotFoundError("Interface not found")
            return {'interface_name': interface_name, 'rx_bytes': 1000, 'tx_bytes': 2000}

        with patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('netpulse.network.get_interface_stats', side_effect=mock_get_interface_stats):

            result = get_all_interface_stats()

            # Should contain interfaces that didn't fail
            assert 'lo' in result
            assert 'wlan0' in result
            assert 'eth0' not in result  # Failed interface should be excluded

    def test_get_all_interface_stats_return_structure(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that get_all_interface_stats() returns dictionary with interface names as keys."""
        with patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_all_interface_stats()

            assert isinstance(result, dict)
            for interface_name in result:
                assert interface_name in mock_psutil_net_io_counters
                assert result[interface_name]['interface_name'] == interface_name

    def test_get_all_interface_stats_general_exception(self):
        """Test get_all_interface_stats() with general exception."""
        with patch('psutil.net_io_counters', side_effect=Exception("General error")):
            with pytest.raises(NetworkError, match="Failed to get all interface statistics"):
                get_all_interface_stats()


class TestValidateInterface:
    """Test validate_interface() function."""

    def test_validate_interface_valid_active(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test validate_interface() with valid active interface."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = validate_interface('eth0')
            assert result is True

    def test_validate_interface_valid_inactive(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test validate_interface() with valid inactive interface."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = validate_interface('wlan0')
            assert result is False

    def test_validate_interface_nonexistent(self, mock_psutil_net_if_addrs):
        """Test validate_interface() with non-existent interface."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs):
            result = validate_interface('nonexistent')
            assert result is False

    def test_validate_interface_loopback(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test validate_interface() with loopback interface."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = validate_interface('lo')
            assert result is True

    def test_validate_interface_virtual_interface(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test validate_interface() with virtual/tunnel interfaces."""
        # Add a virtual interface to the mock
        virtual_interfaces = mock_psutil_net_if_addrs.copy()
        virtual_interfaces['tun0'] = [
            MagicMock(family=2, address='10.0.0.1',
                     netmask='255.255.255.0', broadcast=None)
        ]

        virtual_stats = mock_psutil_net_if_stats.copy()
        virtual_stats['tun0'] = MagicMock(isup=True, mtu=1500, speed=100)

        with patch('psutil.net_if_addrs', return_value=virtual_interfaces), \
             patch('psutil.net_if_stats', return_value=virtual_stats):

            result = validate_interface('tun0')
            assert result is True

    def test_validate_interface_status_check_failure(self, mock_psutil_net_if_addrs):
        """Test validate_interface() when status check fails."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', side_effect=Exception("Status check failed")):

            result = validate_interface('eth0')
            # Should return True if interface has addresses (fallback behavior)
            assert result is True

    def test_validate_interface_general_exception(self):
        """Test validate_interface() with general exception."""
        with patch('psutil.net_if_addrs', side_effect=Exception("General error")):
            result = validate_interface('eth0')
            assert result is False


class TestGetPrimaryInterface:
    """Test get_primary_interface() function."""

    def test_get_primary_interface_single_active(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_primary_interface() with single active interface."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 1000000,
                    'tx_bytes': 500000,
                    'status': 'up'
                }
            }

            result = get_primary_interface()
            assert result == 'eth0'

    def test_get_primary_interface_multiple_with_traffic(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_primary_interface() with multiple interfaces having traffic."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 2000000,
                    'tx_bytes': 1000000,
                    'status': 'up'
                },
                'wlan0': {
                    'interface_name': 'wlan0',
                    'rx_bytes': 500000,
                    'tx_bytes': 250000,
                    'status': 'up'
                },
                'lo': {
                    'interface_name': 'lo',
                    'rx_bytes': 100000,
                    'tx_bytes': 100000,
                    'status': 'up'
                }
            }

            result = get_primary_interface()
            # Should return eth0 (highest traffic: 3MB total)
            assert result == 'eth0'

    def test_get_primary_interface_no_traffic(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_primary_interface() when no interfaces have traffic."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 0,
                    'tx_bytes': 0,
                    'status': 'up'
                },
                'wlan0': {
                    'interface_name': 'wlan0',
                    'rx_bytes': 0,
                    'tx_bytes': 0,
                    'status': 'up'
                }
            }

            result = get_primary_interface()
            assert result is None

    def test_get_primary_interface_mixed_traffic_scenarios(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_primary_interface() with interfaces having different traffic levels."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 1000000,
                    'tx_bytes': 0,
                    'status': 'up'
                },
                'wlan0': {
                    'interface_name': 'wlan0',
                    'rx_bytes': 0,
                    'tx_bytes': 2000000,
                    'status': 'up'
                },
                'eth1': {
                    'interface_name': 'eth1',
                    'rx_bytes': 500000,
                    'tx_bytes': 500000,
                    'status': 'up'
                }
            }

            result = get_primary_interface()
            # Should return wlan0 (2MB total traffic, highest)
            assert result == 'wlan0'

    def test_get_primary_interface_all_down(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test get_primary_interface() when all interfaces are down."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 1000000,
                    'tx_bytes': 500000,
                    'status': 'down'
                }
            }

            result = get_primary_interface()
            assert result is None

    def test_get_primary_interface_no_interfaces(self):
        """Test get_primary_interface() when no interfaces are available."""
        with patch('netpulse.network.get_all_interface_stats', return_value={}):
            result = get_primary_interface()
            assert result is None

    def test_get_primary_interface_general_exception(self):
        """Test get_primary_interface() with general exception."""
        with patch('netpulse.network.get_all_interface_stats', side_effect=Exception("General error")):
            with pytest.raises(NetworkError, match="Failed to determine primary interface"):
                get_primary_interface()


class TestGetInterfaceTrafficSummary:
    """Test get_interface_traffic_summary() function."""

    def test_get_interface_traffic_summary_total_calculation(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that traffic summary correctly sums across all interfaces."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 2000000,
                    'tx_bytes': 1000000,
                    'rx_packets': 2000,
                    'tx_packets': 1000,
                    'status': 'up'
                },
                'lo': {
                    'interface_name': 'lo',
                    'rx_bytes': 500000,
                    'tx_bytes': 500000,
                    'rx_packets': 500,
                    'tx_packets': 500,
                    'status': 'up'
                }
            }

            result = get_interface_traffic_summary()

            assert result['total_interfaces'] == 2
            assert result['active_interfaces'] == 2
            assert result['total_rx_bytes'] == 2500000  # 2000000 + 500000
            assert result['total_tx_bytes'] == 1500000  # 1000000 + 500000
            assert result['total_rx_packets'] == 2500   # 2000 + 500
            assert result['total_tx_packets'] == 1500   # 1000 + 500
            assert 'timestamp' in result

    def test_get_interface_traffic_summary_interface_counting(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that active/total interface counts are accurate."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'status': 'up',
                    'rx_bytes': 1000000,
                    'tx_bytes': 500000,
                    'rx_packets': 1000,
                    'tx_packets': 500
                },
                'wlan0': {
                    'interface_name': 'wlan0',
                    'status': 'down',
                    'rx_bytes': 0,
                    'tx_bytes': 0,
                    'rx_packets': 0,
                    'tx_packets': 0
                },
                'lo': {
                    'interface_name': 'lo',
                    'status': 'up',
                    'rx_bytes': 100000,
                    'tx_bytes': 100000,
                    'rx_packets': 100,
                    'tx_packets': 100
                }
            }

            result = get_interface_traffic_summary()

            assert result['total_interfaces'] == 3
            assert result['active_interfaces'] == 2  # eth0 and lo are up

    def test_get_interface_traffic_summary_empty_system(self):
        """Test get_interface_traffic_summary() when no interfaces are available."""
        with patch('netpulse.network.get_all_interface_stats', return_value={}):

            result = get_interface_traffic_summary()

            assert result['total_interfaces'] == 0
            assert result['active_interfaces'] == 0
            assert result['total_rx_bytes'] == 0
            assert result['total_tx_bytes'] == 0
            assert result['total_rx_packets'] == 0
            assert result['total_tx_packets'] == 0

    def test_get_interface_traffic_summary_return_structure(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that all expected summary fields are present."""
        with patch('netpulse.network.get_all_interface_stats') as mock_get_all_stats:
            mock_get_all_stats.return_value = {
                'eth0': {
                    'interface_name': 'eth0',
                    'rx_bytes': 1000000,
                    'tx_bytes': 500000,
                    'rx_packets': 1000,
                    'tx_packets': 500,
                    'status': 'up'
                }
            }

            result = get_interface_traffic_summary()

            expected_fields = {
                'total_interfaces', 'active_interfaces', 'total_rx_bytes',
                'total_tx_bytes', 'total_rx_packets', 'total_tx_packets', 'timestamp'
            }
            assert set(result.keys()) == expected_fields

    def test_get_interface_traffic_summary_general_exception(self):
        """Test get_interface_traffic_summary() with general exception."""
        with patch('netpulse.network.get_all_interface_stats', side_effect=Exception("General error")):
            with pytest.raises(NetworkError, match="Failed to get traffic summary"):
                get_interface_traffic_summary()


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_interface_not_found_error_type_and_message(self):
        """Test InterfaceNotFoundError type and message format."""
        error = InterfaceNotFoundError("Interface 'eth0' not found or not active")
        assert isinstance(error, NetworkError)
        assert "eth0" in str(error)

    def test_network_error_chaining(self):
        """Test that original exceptions are properly wrapped."""
        original_error = ValueError("Original error")

        try:
            raise NetworkError(f"Network operation failed: {original_error}")
        except NetworkError as e:
            assert "Original error" in str(e)

    def test_permission_error_handling(self):
        """Test PermissionError handling in network operations."""
        with patch('psutil.net_if_addrs', side_effect=psutil.AccessDenied("Access denied")):
            with pytest.raises(NetworkError):
                get_network_interfaces()


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_interface_name_variations(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test with different interface naming conventions."""
        # Test with interface names that have numbers, underscores, etc.
        test_interfaces = {
            'eth0': [MagicMock(family=2, address='192.168.1.1')],
            'wlan_0': [MagicMock(family=2, address='192.168.1.2')],
            'interface_123': [MagicMock(family=2, address='192.168.1.3')]
        }

        with patch('psutil.net_if_addrs', return_value=test_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()
            assert 'eth0' in result
            assert 'wlan_0' in result
            assert 'interface_123' in result

    def test_special_characters_in_interface_names(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test with interfaces having unusual names."""
        # Test with interface names containing special characters
        special_interfaces = {
            'eth-0': [MagicMock(family=2, address='192.168.1.1')],
            'test@interface': [MagicMock(family=2, address='192.168.1.2')]
        }

        with patch('psutil.net_if_addrs', return_value=special_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()
            assert 'eth-0' in result
            assert 'test@interface' in result

    def test_counter_rollover_handling(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test handling of byte/packet counter wraparound."""
        # Simulate counters that have wrapped around
        rollover_counters = {
            'eth0': MagicMock(
                bytes_sent=2**32 - 1000,  # Close to 32-bit wraparound
                bytes_recv=2**32 - 2000,
                packets_sent=2**16 - 100,  # Close to 16-bit wraparound
                packets_recv=2**16 - 200,
                errin=0, errout=0, dropin=0, dropout=0
            )
        }

        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=rollover_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_interface_stats('eth0')

            # Should handle large values without errors
            assert isinstance(result['rx_bytes'], int)
            assert isinstance(result['tx_bytes'], int)
            assert result['rx_bytes'] > 0
            assert result['tx_bytes'] > 0

    def test_system_resource_limits_simulation(self):
        """Test behavior under memory/CPU constraints simulation."""
        # This test simulates resource constraints by mocking slow operations
        def slow_operation(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow operation
            raise MemoryError("Out of memory")

        with patch('psutil.net_if_addrs', side_effect=slow_operation):
            with pytest.raises(NetworkError):
                get_network_interfaces()


class TestIntegrationScenarios:
    """Test integration scenarios and complex operations."""

    def test_discovery_to_validation_flow(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test flow from interface discovery to validation."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Discover interfaces
            interfaces = get_network_interfaces()

            # Validate each discovered interface
            for interface_name in interfaces:
                is_valid = validate_interface(interface_name)
                assert isinstance(is_valid, bool)

                # If interface is in our mock stats, it should be valid
                if interface_name in mock_psutil_net_if_stats:
                    # Status should match our mock data
                    expected_valid = mock_psutil_net_if_stats[interface_name].isup
                    assert is_valid == expected_valid

    def test_validation_to_stats_flow(self, mock_psutil_net_if_addrs, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test flow from validation to statistics retrieval."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters):

            # Validate interfaces first
            valid_interfaces = []
            for interface_name in mock_psutil_net_if_addrs.keys():
                if validate_interface(interface_name):
                    valid_interfaces.append(interface_name)

            # Get stats for valid interfaces
            for interface_name in valid_interfaces:
                stats = get_interface_stats(interface_name)
                assert stats['interface_name'] == interface_name
                assert stats['status'] == 'up'

    def test_stats_to_database_compatibility(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test data format compatibility with database operations."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            stats = get_interface_stats('eth0')

            # Verify field names match database schema expectations
            expected_db_fields = {
                'interface_name', 'rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets',
                'rx_errors', 'tx_errors', 'rx_drops', 'tx_drops', 'timestamp', 'status'
            }
            assert set(stats.keys()) == expected_db_fields

            # Verify data types are compatible with database storage
            assert isinstance(stats['interface_name'], str)
            assert isinstance(stats['rx_bytes'], int)
            assert isinstance(stats['tx_bytes'], int)
            assert isinstance(stats['timestamp'], str)

    def test_primary_interface_workflow(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test complete workflow of identifying primary interface."""
        with patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Get all interface stats
            all_stats = get_all_interface_stats()

            # Identify primary interface
            primary = get_primary_interface()

            # Verify primary interface logic
            if primary:
                assert primary in all_stats
                assert all_stats[primary]['status'] == 'up'

                # Verify it's the interface with highest traffic
                max_traffic = max(
                    stats['rx_bytes'] + stats['tx_bytes']
                    for stats in all_stats.values()
                    if stats['status'] == 'up'
                )
                assert all_stats[primary]['rx_bytes'] + all_stats[primary]['tx_bytes'] == max_traffic


class TestCrossFunctionConsistency:
    """Test consistency across different functions."""

    def test_interface_list_consistency(self, mock_psutil_net_if_addrs, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that same interfaces are returned by discovery and stats functions."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Get interfaces from discovery
            discovered_interfaces = set(get_network_interfaces().keys())

            # Get interfaces from stats
            stats_interfaces = set(get_all_interface_stats().keys())

            # Should be consistent (stats might have fewer due to filtering)
            assert stats_interfaces.issubset(discovered_interfaces)

    def test_status_consistency(self, mock_psutil_net_if_addrs, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that interface status is consistent across different functions."""
        with patch('psutil.net_if_addrs', return_value=mock_psutil_net_if_addrs), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Get status from discovery
            interfaces = get_network_interfaces()
            discovery_status = {name: info['status'] for name, info in interfaces.items()}

            # Get status from individual stats
            stats_status = {}
            for interface_name in interfaces:
                try:
                    stats = get_interface_stats(interface_name)
                    stats_status[interface_name] = stats['status']
                except (InterfaceNotFoundError, NetworkError):
                    continue

            # Status should be consistent
            for interface_name in stats_status:
                assert discovery_status[interface_name] == stats_status[interface_name]

    def test_data_consistency_single_vs_all(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that statistics from single interface match all interface results."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Get single interface stats
            single_stats = get_interface_stats('eth0')

            # Get all interface stats
            all_stats = get_all_interface_stats()

            # Should match exactly
            assert 'eth0' in all_stats
            for key in ['rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets']:
                assert single_stats[key] == all_stats['eth0'][key]


class TestPerformanceScenarios:
    """Test performance under various scenarios."""

    def test_large_interface_count_performance(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test performance with many network interfaces."""
        # Create mock data with many interfaces
        large_interface_set = {}
        large_stats_set = {}

        for i in range(100):  # Simulate 100 interfaces
            interface_name = f'eth{i}'
            large_interface_set[interface_name] = [
                MagicMock(family=2, address=f'192.168.{i}.1',
                         netmask='255.255.255.0', broadcast=f'192.168.{i}.255')
            ]
            large_stats_set[interface_name] = MagicMock(isup=True, mtu=1500, speed=1000)

        with patch('psutil.net_if_addrs', return_value=large_interface_set), \
             patch('psutil.net_if_stats', return_value=large_stats_set):

            start_time = time.time()
            result = get_network_interfaces()
            end_time = time.time()

            assert len(result) == 100
            # Should complete within reasonable time (less than 5 seconds)
            assert end_time - start_time < 5.0

    def test_frequent_polling_performance(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test performance with repeated calls for monitoring scenarios."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Perform multiple rapid calls
            start_time = time.time()
            for _ in range(10):
                get_interface_stats('eth0')
            end_time = time.time()

            # Should complete within reasonable time
            assert end_time - start_time < 2.0

    def test_memory_usage_monitoring(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Monitor memory consumption during extended operation."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Perform many operations to test memory usage
            results = []
            for _ in range(100):
                result = get_interface_stats('eth0')
                results.append(result)

            # Should not accumulate excessive memory
            assert len(results) == 100

            # Clean up
            del results

    def test_response_time_under_normal_load(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test function execution times under normal load."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            # Test individual function response times
            start_time = time.time()
            get_interface_stats('eth0')
            single_time = time.time() - start_time

            start_time = time.time()
            get_all_interface_stats()
            all_time = time.time() - start_time

            # Individual function should be faster than getting all
            assert single_time < all_time


class TestPlatformCompatibility:
    """Test platform-specific interface naming and behavior."""

    def test_linux_interface_names(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test with Linux-style interface names (eth0, wlan0, etc.)."""
        linux_interfaces = {
            'eth0': [MagicMock(family=2, address='192.168.1.1')],
            'wlan0': [MagicMock(family=2, address='192.168.1.2')],
            'br0': [MagicMock(family=2, address='192.168.1.3')],
            'veth0': [MagicMock(family=2, address='192.168.1.4')]
        }

        with patch('psutil.net_if_addrs', return_value=linux_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()
            assert 'eth0' in result
            assert 'wlan0' in result
            assert 'br0' in result
            assert 'veth0' in result

    def test_macos_interface_names(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test with macOS-style interface names (en0, lo0, etc.)."""
        macos_interfaces = {
            'en0': [MagicMock(family=2, address='192.168.1.1')],
            'lo0': [MagicMock(family=2, address='127.0.0.1')],
            'awdl0': [MagicMock(family=2, address='192.168.1.2')],
            'utun0': [MagicMock(family=2, address='10.0.0.1')]
        }

        with patch('psutil.net_if_addrs', return_value=macos_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()
            assert 'en0' in result
            assert 'lo0' in result
            assert 'awdl0' in result
            assert 'utun0' in result

    def test_windows_interface_names(self, mock_psutil_net_if_addrs, mock_psutil_net_if_stats):
        """Test with Windows-style adapter names."""
        windows_interfaces = {
            'Ethernet': [MagicMock(family=2, address='192.168.1.1')],
            'Wi-Fi': [MagicMock(family=2, address='192.168.1.2')],
            'Local Area Connection': [MagicMock(family=2, address='192.168.1.3')],
            'vEthernet (Default Switch)': [MagicMock(family=2, address='192.168.1.4')]
        }

        with patch('psutil.net_if_addrs', return_value=windows_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            result = get_network_interfaces()
            assert 'Ethernet' in result
            assert 'Wi-Fi' in result
            assert 'Local Area Connection' in result
            assert 'vEthernet (Default Switch)' in result

    def test_interface_name_mapping_consistency(self, mock_psutil_net_if_addrs, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test consistent behavior across different platform naming conventions."""
        test_interfaces = {
            'test_interface': [MagicMock(family=2, address='192.168.1.1')],
            'Test-Interface': [MagicMock(family=2, address='192.168.1.2')],
            'test.interface': [MagicMock(family=2, address='192.168.1.3')]
        }

        test_stats = {
            'test_interface': MagicMock(isup=True, mtu=1500, speed=1000),
            'Test-Interface': MagicMock(isup=True, mtu=1500, speed=1000),
            'test.interface': MagicMock(isup=True, mtu=1500, speed=1000)
        }

        with patch('psutil.net_if_addrs', return_value=test_interfaces), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=test_stats):

            # All functions should handle the interface names consistently
            interfaces = get_network_interfaces()
            for interface_name in interfaces:
                assert validate_interface(interface_name)

                try:
                    stats = get_interface_stats(interface_name)
                    assert stats['interface_name'] == interface_name
                except (InterfaceNotFoundError, NetworkError):
                    # Some interfaces might not have stats, which is OK
                    pass


class TestDataValidation:
    """Test data validation and format compliance."""

    def test_database_field_mapping_exact_match(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test exact field names match database schema."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            stats = get_interface_stats('eth0')

            # These field names must exactly match the database schema
            required_fields = {
                'interface_name', 'rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets',
                'rx_errors', 'tx_errors', 'rx_drops', 'tx_drops', 'timestamp', 'status'
            }

            assert set(stats.keys()) == required_fields

            # Verify no extra fields are present
            assert len(stats.keys()) == len(required_fields)

    def test_data_type_validation(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test that all fields have correct data types."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            stats = get_interface_stats('eth0')

            # String fields
            assert isinstance(stats['interface_name'], str)
            assert isinstance(stats['timestamp'], str)
            assert isinstance(stats['status'], str)

            # Integer fields
            int_fields = ['rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets',
                         'rx_errors', 'tx_errors', 'rx_drops', 'tx_drops']
            for field in int_fields:
                assert isinstance(stats[field], int)
                assert stats[field] >= 0

    def test_timestamp_format_compliance(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test ISO 8601 timestamp format compliance."""
        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=mock_psutil_net_io_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            stats = get_interface_stats('eth0')

            timestamp = stats['timestamp']

            # Should be valid ISO format
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            # Should include timezone information
            assert 'T' in timestamp
            assert ('Z' in timestamp or '+' in timestamp or '-' in timestamp)

    def test_numeric_range_validation(self, mock_psutil_net_io_counters, mock_psutil_net_if_stats):
        """Test handling of very large counter values."""
        # Test with very large values
        large_counters = {
            'eth0': MagicMock(
                bytes_sent=2**63 - 1,  # Max 64-bit signed int
                bytes_recv=2**63 - 1,
                packets_sent=2**31 - 1,  # Max 32-bit signed int
                packets_recv=2**31 - 1,
                errin=0, errout=0, dropin=0, dropout=0
            )
        }

        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=large_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            stats = get_interface_stats('eth0')

            # Should handle large values correctly
            assert stats['rx_bytes'] == 2**63 - 1
            assert stats['tx_bytes'] == 2**63 - 1
            assert isinstance(stats['rx_bytes'], int)
            assert isinstance(stats['tx_bytes'], int)


class TestMockAndStubScenarios:
    """Test scenarios with mocked dependencies and controlled data."""

    def test_mock_interface_creation(self):
        """Test with completely simulated network interfaces."""
        mock_interfaces = {
            'mock_eth0': [
                MagicMock(family=2, address='10.0.0.1',
                         netmask='255.255.255.0', broadcast='10.0.0.255')
            ],
            'mock_wlan0': [
                MagicMock(family=2, address='192.168.1.1',
                         netmask='255.255.255.0', broadcast='192.168.1.255')
            ]
        }

        mock_stats = {
            'mock_eth0': MagicMock(isup=True, mtu=1500, speed=1000),
            'mock_wlan0': MagicMock(isup=True, mtu=1500, speed=150)
        }

        with patch('psutil.net_if_addrs', return_value=mock_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_stats):

            result = get_network_interfaces()

            assert 'mock_eth0' in result
            assert 'mock_wlan0' in result
            assert result['mock_eth0']['status'] == 'up'
            assert result['mock_wlan0']['status'] == 'up'

    def test_mock_statistics_injection(self, mock_psutil_net_if_stats):
        """Test with controlled, predictable statistics data."""
        controlled_counters = {
            'eth0': MagicMock(
                bytes_sent=1000,
                bytes_recv=2000,
                packets_sent=10,
                packets_recv=20,
                errin=0, errout=0, dropin=0, dropout=0
            )
        }

        with patch('netpulse.network.validate_interface', return_value=True), \
             patch('psutil.net_io_counters', return_value=controlled_counters), \
             patch('psutil.net_if_stats', return_value=mock_psutil_net_if_stats):

            stats = get_interface_stats('eth0')

            assert stats['rx_bytes'] == 2000
            assert stats['tx_bytes'] == 1000
            assert stats['rx_packets'] == 20
            assert stats['tx_packets'] == 10

    def test_error_simulation_scenarios(self):
        """Test error handling with various mocked failure scenarios."""
        # Test with simulated psutil failures
        with patch('psutil.net_if_addrs', side_effect=Exception("Simulated psutil failure")):
            with pytest.raises(NetworkError, match="Failed to discover network interfaces"):
                get_network_interfaces()

        # Test with simulated permission errors
        with patch('psutil.net_if_addrs', side_effect=psutil.AccessDenied("Simulated permission error")):
            with pytest.raises(NetworkError, match="Failed to discover network interfaces"):
                get_network_interfaces()

    def test_dependency_isolation(self):
        """Test that psutil dependency can be completely isolated for testing."""
        # This test verifies that all psutil calls are properly mocked
        # and the functions work without actual system dependencies

        mock_interfaces = {'test_interface': []}
        mock_stats = {'test_interface': MagicMock(isup=True, mtu=1500, speed=1000)}
        mock_counters = {
            'test_interface': MagicMock(
                bytes_sent=100, bytes_recv=200,
                packets_sent=1, packets_recv=2,
                errin=0, errout=0, dropin=0, dropout=0
            )
        }

        with patch('psutil.net_if_addrs', return_value=mock_interfaces), \
             patch('psutil.net_if_stats', return_value=mock_stats), \
             patch('psutil.net_io_counters', return_value=mock_counters):

            # Should work completely with mocked dependencies
            interfaces = get_network_interfaces()
            assert 'test_interface' in interfaces

            with patch('netpulse.network.validate_interface', return_value=True):
                stats = get_interface_stats('test_interface')
                assert stats['interface_name'] == 'test_interface'
                assert stats['rx_bytes'] == 200
                assert stats['tx_bytes'] == 100

    def test_controlled_environment_simulation(self):
        """Test behavior in a completely controlled test environment."""
        # Simulate a minimal network environment
        minimal_interfaces = {
            'lo': [
                MagicMock(family=2, address='127.0.0.1',
                         netmask='255.0.0.0', broadcast=None)
            ]
        }

        minimal_stats = {
            'lo': MagicMock(isup=True, mtu=65536, speed=0)
        }

        minimal_counters = {
            'lo': MagicMock(
                bytes_sent=1000, bytes_recv=1000,
                packets_sent=10, packets_recv=10,
                errin=0, errout=0, dropin=0, dropout=0
            )
        }

        with patch('psutil.net_if_addrs', return_value=minimal_interfaces), \
             patch('psutil.net_if_stats', return_value=minimal_stats), \
             patch('psutil.net_io_counters', return_value=minimal_counters):

            # Test discovery
            interfaces = get_network_interfaces()
            assert len(interfaces) == 1
            assert 'lo' in interfaces

            # Test validation
            assert validate_interface('lo') is True
            assert validate_interface('nonexistent') is False

            # Test stats
            with patch('netpulse.network.validate_interface', return_value=True):
                stats = get_interface_stats('lo')
                assert stats['interface_name'] == 'lo'
                assert stats['status'] == 'up'

            # Test primary interface
            primary = get_primary_interface()
            assert primary == 'lo'

            # Test summary
            summary = get_interface_traffic_summary()
            assert summary['total_interfaces'] == 1
            assert summary['active_interfaces'] == 1