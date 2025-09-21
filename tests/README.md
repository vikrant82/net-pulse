# Net-Pulse Test Suite

This directory contains the comprehensive test suite for the Net-Pulse application.

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Pytest configuration and fixtures
├── README.md                # This file
├── test_api.py              # **API Endpoints tests (40+ tests)**
├── test_autodetect.py       # **Auto-Detection Logic tests (14 tests)**
├── test_collector.py        # **Core Polling Engine tests (73 tests)**
├── test_database.py         # Tests for database module (comprehensive CRUD operations)
├── test_integration.py      # **Comprehensive Integration Tests (50+ tests)**
├── test_main.py             # Tests for main application module
├── test_network.py          # Tests for network module (comprehensive interface testing)
├── test_init.py             # Tests for package initialization
├── test_utils.py            # Test utilities and helper functions
└── test_test_utils.py       # Tests for test utilities
```

### Test Module Overview

- **`test_api.py`** (40+ tests) - **API Endpoints Testing** - Comprehensive testing of all API endpoints including:
  - Interface management endpoints (GET /api/interfaces, etc.)
  - Traffic data endpoints (GET /api/traffic/*)
  - Configuration endpoints (GET/PUT /api/config/*)
  - System information endpoints (GET /api/system/*)
  - Error handling and response validation
  - Integration tests for API workflows

- **`test_collector.py`** (73 tests) - **Core Polling Engine** - Comprehensive NetworkDataCollector testing including:
  - Core functionality: Initialization, scheduler setup, start/stop operations, manual collection, status reporting
  - Configuration management: Default config, interface configuration, polling interval config, retry configuration, dynamic config updates
  - Collection logic: Interface discovery, multi-interface collection, interface filtering, traffic data structure
  - Delta calculation: Basic delta calculation, counter rollover handling, time-based deltas, zero traffic handling
  - Error handling & resilience: Network errors, database errors, scheduler errors, partial failures, graceful degradation
  - Statistics & monitoring: Collection metrics, interface counts, error counting, performance metrics, status reporting
  - Integration tests: Database integration, network module integration, configuration persistence, data integrity
  - Edge cases & boundary tests: Empty interface list, single interface, counter reset, system limits, large values
  - Mocking strategy: Network interface mocking, database mocking, time mocking, scheduler mocking
  - Test data: Sample network data, configuration data, error scenarios, comprehensive fixtures
  - **95%+ code coverage** with platform-independent testing

- **`test_database.py`** (45 tests) - Comprehensive database testing including:
  - Connection management and error handling
  - Schema initialization and table creation
  - CRUD operations for traffic data and configuration
  - Edge cases and integration scenarios
  - 97% code coverage

- **`test_network.py`** (80 tests) - Comprehensive network module testing including:
  - Network interface discovery and validation
  - Traffic statistics collection and processing
  - Error handling and custom exceptions
  - Edge cases and platform compatibility testing
  - Integration scenarios and cross-function consistency
  - Performance testing and data validation
  - Mock and stub scenarios for dependency isolation
  - 100% test success rate

- **`test_api.py`** (40+ tests) - Comprehensive API endpoint testing:
  - Interface management endpoints (8 tests)
  - Traffic data endpoints (6 tests)
  - Configuration endpoints (8 tests)
  - System information endpoints (6 tests)
  - Error handling and integration tests (12+ tests)

- **`test_main.py`** (15 tests) - Main application testing:
  - FastAPI application creation
  - API endpoints and routing
  - Application configuration

- **`test_autodetect.py`** (14 tests) - **Auto-Detection Logic** - Comprehensive testing of intelligent network interface discovery including:
  - **Unit Tests** (9 tests): InterfaceAnalyzer initialization, interface validation logic, configuration serialization, error handling
  - **Integration Tests** (5 tests): Real network interface discovery, traffic pattern analysis, database configuration, complete workflow testing
  - **Core Features**: Interface discovery and filtering, primary interface identification, activity analysis, configuration management
  - **Error Handling**: Network errors, database errors, invalid interfaces, graceful degradation
  - **Integration**: Database integration, network module integration, configuration persistence, real-world workflow testing
  - **Test Strategy**: Mix of unit tests for core logic and integration tests for real-world functionality

- **`test_utils.py`** - Utility functions and helpers
- **`test_test_utils.py`** - Testing utilities and fixtures
- **`test_init.py`** - Package initialization tests

- **`test_integration.py`** (50+ tests) - **Comprehensive Integration Testing** - Complete workflow validation including:
  - **End-to-End Workflow Tests**: Complete data collection cycle, auto-detection workflow, configuration initialization
  - **Cross-Module Integration Tests**: Network→Database, Auto-detection→Network→Database, Collector→Network→Database workflows
  - **Real-World Scenario Tests**: First-time setup, interface monitoring, database persistence, configuration updates
  - **Performance and Load Integration Tests**: Continuous collection, multiple interface monitoring, database performance
  - **Error Recovery Integration Tests**: Network failures, database issues, configuration corruption, graceful degradation
  - **System-Level Integration Tests**: Application startup, background scheduler, health monitoring, graceful shutdown
  - **Data Integrity Tests**: Traffic data consistency, configuration persistence, interface statistics accuracy
  - **Concurrent Operation Tests**: Multiple collection cycles, concurrent auto-detection, configuration updates during collection
  - **Real System Integration**: Uses actual network interfaces and database operations for authentic testing
  - **Comprehensive Coverage**: Tests complete Net-Pulse workflow from interface discovery to database storage

## Auto-Detection Test Suite

### Overview
The `test_autodetect.py` module provides comprehensive testing for Net-Pulse's intelligent auto-detection functionality, which automatically discovers network interfaces, analyzes traffic patterns, and configures the system for optimal performance.

### Test Structure (50+ tests total)

#### Unit Tests (9 tests)
- **`TestInterfaceAnalyzer`** - Core functionality testing
  - `test_analyzer_initialization` - InterfaceAnalyzer setup and configuration
  - `test_is_valid_interface_filtering` - Interface validation logic and filtering
  - `test_populate_initial_config_no_interfaces` - Configuration handling with no interfaces
  - `test_serialize_interface_config` - Interface configuration serialization
  - `test_analyzer_initialization` - Component initialization and dependencies

#### Integration Tests (5 tests)
- **`TestAutoDetectionIntegration`** - Real-world functionality testing
  - `test_auto_detection_initialization_integration` - Complete auto-detection workflow
  - `test_interface_analyzer_integration` - InterfaceAnalyzer real-world integration
  - `test_configuration_management_integration` - Configuration persistence and management
  - `test_error_handling_integration` - Error handling and robustness
  - `test_auto_detection_workflow_integration` - End-to-end workflow testing

### Key Features Tested

#### Core Auto-Detection Functionality
- **Interface Discovery**: Automatic detection of all available network interfaces
- **Smart Filtering**: Exclusion of loopback, docker, and inactive interfaces
- **Traffic Analysis**: Real-time monitoring and analysis of interface activity
- **Primary Interface Identification**: Selection of most active interface based on traffic patterns
- **Configuration Management**: Automatic population of initial configuration settings

#### Integration Testing
- **Real Network Operations**: Tests use actual network interfaces and traffic data
- **Database Integration**: Configuration persistence and retrieval testing
- **Error Scenarios**: Robustness testing with various failure conditions
- **Workflow Testing**: Complete end-to-end auto-detection process validation

#### Performance Characteristics
- **Integration Test Duration**: ~3-4 minutes (due to real network operations)
- **Real Interface Discovery**: Tests actual system interfaces
- **Traffic Pattern Analysis**: Monitors real network traffic
- **Database Operations**: Performs actual configuration storage/retrieval

### Running Auto-Detection Tests

```bash
# Run all auto-detection tests
pytest tests/test_autodetect.py -v

# Run only unit tests (fast)
pytest tests/test_autodetect.py::TestInterfaceAnalyzer -v

# Run only integration tests (slower, more comprehensive)
pytest tests/test_autodetect.py::TestAutoDetectionIntegration -v

# Run with coverage
pytest tests/test_autodetect.py --cov=src/netpulse/autodetect --cov-report=html
```

### Test Significance

The auto-detection tests are crucial because they:
- **Validate Real Functionality**: Test actual network interface discovery and analysis
- **Ensure System Integration**: Verify proper integration with network and database modules
- **Test Self-Configuration**: Confirm the system can configure itself automatically
- **Validate Error Handling**: Ensure graceful handling of various error conditions
- **Performance Verification**: Test real-world performance characteristics

### Integration Test Notes

- **Time-Intensive**: Integration tests take longer due to real network operations
- **Environment Dependent**: Results may vary based on system network configuration
- **Real Data**: Tests use actual network interfaces and traffic patterns
- **Robustness**: Designed to handle various network configurations gracefully

## Comprehensive Integration Test Suite

### Overview
The `test_integration.py` module provides comprehensive integration testing for the complete Net-Pulse data collection workflow. This test suite validates the entire system from interface discovery through database storage and API endpoints.

### Test Structure (50+ tests total)

#### End-to-End Workflow Tests
- **`TestEndToEndWorkflow`** - Complete system workflow validation
  - `test_complete_data_collection_cycle` - Full workflow from discovery to storage
  - `test_auto_detection_workflow_integration` - Auto-detection and configuration
  - `test_configuration_initialization_and_interface_selection_workflow` - Config management

#### Cross-Module Integration Tests
- **`TestCrossModuleIntegration`** - Inter-module workflow validation
  - `test_network_module_to_database_module_integration` - Network→Database workflow
  - `test_auto_detection_to_network_to_database_workflow` - Complete auto-detection workflow
  - `test_collector_to_network_to_database_workflow` - Collector orchestration
  - `test_configuration_management_across_all_modules` - Cross-module configuration

#### Real-World Scenario Tests
- **`TestRealWorldScenarios`** - Practical usage scenarios
  - `test_first_time_setup_and_auto_detection_workflow` - Initial system setup
  - `test_interface_monitoring_with_real_network_traffic` - Real traffic monitoring
  - `test_database_persistence_and_data_retrieval` - Data persistence testing
  - `test_configuration_updates_and_interface_changes` - Dynamic configuration

#### Performance and Load Integration Tests
- **`TestPerformanceAndLoadIntegration`** - System performance validation
  - `test_continuous_data_collection_over_extended_periods` - Long-term collection
  - `test_multiple_interface_monitoring_scenarios` - Multi-interface performance
  - `test_database_growth_and_query_performance` - Database scaling
  - `test_memory_usage_and_resource_consumption_patterns` - Resource efficiency

#### Error Recovery Integration Tests
- **`TestErrorRecoveryIntegration`** - System resilience testing
  - `test_network_interface_failures_during_collection` - Network failure handling
  - `test_database_connection_issues_during_operation` - Database failure recovery
  - `test_configuration_corruption_and_recovery` - Configuration error recovery
  - `test_partial_system_failures_and_graceful_degradation` - Partial failure handling

#### System-Level Integration Tests
- **`TestSystemLevelIntegration`** - Complete system validation
  - `test_application_startup_and_initialization` - System startup sequence
  - `test_background_scheduler_and_data_collection` - Scheduler functionality
  - `test_health_monitoring_and_status_reporting` - Health monitoring
  - `test_graceful_shutdown_and_cleanup` - System shutdown

#### Data Integrity Tests
- **`TestDataIntegrity`** - Data quality validation
  - `test_traffic_data_consistency_across_collection_cycles` - Data consistency
  - `test_configuration_persistence_and_retrieval_accuracy` - Configuration integrity
  - `test_interface_statistics_accuracy_and_completeness` - Statistics validation
  - `test_database_relationships_and_constraints_validation` - Database integrity

#### Concurrent Operation Tests
- **`TestConcurrentOperation`** - Multi-threading and concurrency
  - `test_multiple_collection_cycles_running_simultaneously` - Concurrent collection
  - `test_interface_auto_detection_during_active_collection` - Concurrent operations
  - `test_configuration_updates_during_data_collection` - Dynamic updates
  - `test_database_operations_during_network_monitoring` - Concurrent DB operations

### Key Features Tested

#### Complete Workflow Coverage
- **Interface Discovery**: Automatic detection of all available network interfaces
- **Auto-Detection**: Intelligent interface analysis and primary interface identification
- **Configuration Management**: Initial configuration population and dynamic updates
- **Data Collection**: Background scheduling and traffic statistics collection
- **Database Storage**: Data persistence with integrity validation
- **API Integration**: RESTful API endpoints and status reporting
- **Error Handling**: Comprehensive error recovery and graceful degradation

#### Integration Testing Approach
- **Real System Components**: Tests use actual network interfaces and database operations
- **Cross-Module Workflows**: Validates interaction between all system modules
- **Performance Validation**: Tests system performance under various loads
- **Error Scenarios**: Comprehensive testing of failure modes and recovery
- **Concurrent Operations**: Validates system behavior under concurrent load
- **Data Integrity**: Ensures data accuracy and consistency throughout the system

#### Performance Characteristics
- **Integration Test Duration**: ~5-10 minutes (due to real network and database operations)
- **Real Interface Testing**: Uses actual system network interfaces
- **Database Performance**: Tests real database operations and query performance
- **Memory Efficiency**: Validates resource consumption patterns
- **Concurrent Operations**: Tests multi-threaded and concurrent scenarios

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test category
pytest tests/test_integration.py::TestEndToEndWorkflow -v
pytest tests/test_integration.py::TestCrossModuleIntegration -v
pytest tests/test_integration.py::TestRealWorldScenarios -v
pytest tests/test_integration.py::TestPerformanceAndLoadIntegration -v

# Run integration tests with coverage
pytest tests/test_integration.py --cov=src/netpulse --cov-report=html

# Run integration tests only (skip slower performance tests)
pytest tests/test_integration.py -m "not slow"

# Run integration tests with detailed output
pytest tests/test_integration.py -v -s
```

### Test Significance

The integration tests are crucial because they:
- **Validate Complete Workflows**: Test the entire Net-Pulse data collection pipeline
- **Ensure System Integration**: Verify proper interaction between all modules
- **Test Real-World Usage**: Validate system behavior with actual network interfaces
- **Performance Validation**: Ensure system performs well under various loads
- **Error Recovery**: Confirm system resilience and graceful error handling
- **Data Integrity**: Validate data accuracy throughout the collection process
- **Concurrent Operations**: Test system behavior under concurrent load
- **End-to-End Validation**: Provide confidence in complete system functionality

### Integration Test Environment

Integration tests require:
- **Network Access**: Real network interfaces for interface discovery and monitoring
- **Database**: SQLite database for data persistence testing
- **System Resources**: Sufficient resources for performance and load testing
- **Time**: Extended execution time due to real-world operations

### Test Data and Fixtures

Integration tests use:
- **Real Network Interfaces**: Actual system interfaces for authentic testing
- **Database Operations**: Real database insert/query operations
- **Performance Metrics**: Actual timing and resource consumption measurements
- **Error Scenarios**: Simulated failures for recovery testing
- **Concurrent Operations**: Multi-threaded test scenarios

### Troubleshooting Integration Tests

Common issues and solutions:
- **Network Interface Not Found**: Tests may skip if no suitable interfaces are available
- **Database Connection Issues**: Verify SQLite database permissions and path
- **Performance Test Timeouts**: May occur on slower systems, increase timeout values
- **Memory Test Variations**: Memory usage may vary by system, adjust thresholds if needed
- **Concurrent Test Issues**: May require adjusting thread counts for different systems

## Environment Setup

### Quick Setup (Recommended)
Use the provided setup script for the easiest installation:

```bash
# Run the automated setup script
./setup_test_env.sh
```

This script will:
- Create a virtual environment
- Install all test dependencies
- Verify the installation
- Provide usage instructions

### Manual Setup

#### Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install project in development mode with all dependencies
pip install -e .

# Or install only test dependencies
pip install -e ".[test]"
```

### Alternative: Install Test Dependencies Only
```bash
# If you already have the project installed
pip install pytest pytest-cov pytest-mock httpx
```

## Running Tests

### Run all tests
```bash
# Run all tests in the project
pytest

# Run all tests with coverage
pytest --cov=src/netpulse --cov-report=html --cov-report=term-missing

# Run all tests with verbose output
pytest -v

# Run all tests in quiet mode
pytest -q
```

### Run module-level tests
```bash
# Run tests for a specific module
pytest tests/test_autodetect.py    # Auto-Detection Logic tests (14 tests)
pytest tests/test_collector.py     # Core Polling Engine tests (73 tests)
pytest tests/test_database.py      # Database module tests (45 tests)
pytest tests/test_integration.py   # Comprehensive Integration Tests (50+ tests)
pytest tests/test_main.py          # Main application tests (15 tests)
pytest tests/test_network.py       # Network module tests (80 tests)
pytest tests/test_utils.py         # Utility functions tests
pytest tests/test_init.py          # Package initialization tests

# Run multiple specific test files
pytest tests/test_api.py tests/test_autodetect.py tests/test_collector.py tests/test_database.py tests/test_main.py tests/test_network.py tests/test_utils.py

# Run all tests except specific modules
pytest tests/ -k "not test_database"
```

### Run tests by module functionality
```bash
# Auto-Detection Logic tests only
pytest tests/test_autodetect.py

# Core Polling Engine tests only
pytest tests/test_collector.py

# Database-related tests only
pytest tests/test_database.py

# Comprehensive Integration Tests only
pytest tests/test_integration.py

# Main application tests only
pytest tests/test_main.py

# Network module tests only
pytest tests/test_network.py

# Utility and helper tests
pytest tests/test_utils.py tests/test_test_utils.py

# Test utilities and initialization
pytest tests/test_init.py tests/test_test_utils.py
```

### Run tests with specific markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Run slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Run tests with different verbosity
```bash
# Quiet mode
pytest -q

# Verbose mode
pytest -v

# Very verbose mode
pytest -vv

# Show local variables in tracebacks
pytest -l
```

## Dependencies

### Required Test Dependencies
The following packages are required to run the test suite:

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mock utilities for testing
- **httpx** - HTTP client for FastAPI testing

### Installing Dependencies

**Option 1: Install everything (recommended)**
```bash
pip install -e ".[dev]"
```

**Option 2: Install only test dependencies**
```bash
pip install -e ".[test]"
```

**Option 3: Manual installation**
```bash
pip install pytest pytest-cov pytest-mock httpx
```

### Development vs Test Dependencies

- **dev dependencies** (`pip install -e ".[dev]"`) - Includes testing, linting, and formatting tools
- **test dependencies** (`pip install -e ".[test]"`) - Only the minimum required for running tests

## Test Categories

### Unit Tests (`-m unit`)
- Test individual functions and methods
- Fast execution
- No external dependencies

### Integration Tests (`-m integration`)
- Test interaction between components
- May involve external services
- Slower execution
- **Auto-Detection Integration Tests**: Real network interface discovery, traffic pattern analysis, database configuration, complete workflow testing

### API Tests (`-m api`)
- Test API endpoints and responses
- Use test client for HTTP testing
- Verify status codes and response formats

### Slow Tests (`-m slow`)
- Tests that take longer to execute
- Performance tests
- Load tests

## Test Configuration

The test configuration is defined in `pyproject.toml` and includes:

- Coverage reporting (80% minimum)
- Test discovery patterns
- Custom markers
- Warning filters
- Output formatting

## Fixtures

Common fixtures available in `conftest.py`:

- `app`: FastAPI application instance
- `client`: Test client for API testing
- `sample_network_data`: Sample network statistics data
- `mock_network_interface`: Mock network interface for testing
- `test_database_url`: Test database URL

## Test Utilities

The `test_utils.py` module provides:

- `TestDataFactory`: Factory for creating test data
- `APITestHelper`: Helper functions for API testing
- `MockNetworkInterface`: Mock network interface for testing
- `PerformanceTestHelper`: Utilities for performance testing

## Writing Tests

### Best Practices

1. Use descriptive test names that explain what is being tested
2. Follow the Arrange-Act-Assert pattern
3. Use fixtures for common test data and setup
4. Mark slow tests with `@pytest.mark.slow`
5. Include docstrings for test classes and methods
6. Use appropriate assertions for the expected behavior

### Example Test Structure

```python
class TestFeature:
    """Test class for specific feature."""

    def test_feature_works_correctly(self, fixture_name):
        """Test that feature works as expected."""
        # Arrange
        setup_data = fixture_name

        # Act
        result = function_under_test(setup_data)

        # Assert
        assert result == expected_value
```

## Coverage

The project aims for 80% code coverage. Coverage reports are generated in HTML format and can be found in the `htmlcov/` directory after running tests with coverage.

### Coverage Commands

```bash
# Run all tests with coverage (HTML and terminal reports)
pytest --cov=src/netpulse --cov-report=html --cov-report=term-missing

# Run specific test file with coverage
pytest tests/test_collector.py --cov=src/netpulse --cov-report=html --cov-report=term-missing
pytest tests/test_database.py --cov=src/netpulse --cov-report=html --cov-report=term-missing
pytest tests/test_network.py --cov=src/netpulse --cov-report=html --cov-report=term-missing

# Run tests with coverage and fail if below threshold
pytest --cov=src/netpulse --cov-report=html --cov-fail-under=80

# Generate coverage report for specific modules only
pytest --cov=src/netpulse/autodetect --cov=src/netpulse/collector --cov=src/netpulse/database --cov=src/netpulse/network --cov=src/netpulse/main --cov-report=html

# View coverage report in browser (after running with --cov-report=html)
open htmlcov/index.html

# Get coverage summary only
pytest --cov=src/netpulse --cov-report=term-missing
```

### Quick Command Reference

```bash
# 🚀 Most common commands
pytest                                    # Run all tests
pytest -v                                 # Run all tests (verbose)
pytest --cov=src/netpulse                 # Run with coverage
pytest tests/test_autodetect.py -v        # Run auto-detection tests only (14 tests)
pytest tests/test_collector.py -v         # Run collector tests only (73 tests)
pytest tests/test_integration.py -v       # Run integration tests only (50+ tests)

# 📊 Coverage commands
pytest --cov=src/netpulse --cov-report=html --cov-report=term-missing
pytest --cov=src/netpulse --cov-fail-under=80

# 🧪 Module-specific tests
pytest tests/test_api.py                  # API Endpoints (40+ tests)
pytest tests/test_autodetect.py           # Auto-Detection Logic (14 tests)
pytest tests/test_collector.py            # Core Polling Engine (73 tests)
pytest tests/test_database.py             # Database module (45 tests)
pytest tests/test_integration.py          # Comprehensive Integration Tests (50+ tests)
pytest tests/test_main.py                 # Main application (15 tests)
pytest tests/test_network.py              # Network module (80 tests)
pytest tests/test_utils.py                # Utility functions
pytest tests/test_init.py                 # Package initialization

# 🏷️  Test categories
pytest -m unit                            # Unit tests only
pytest -m integration                     # Integration tests only
pytest -m api                             # API tests only
pytest -m "not slow"                      # Skip slow tests

# 📁 Run specific test files
pytest tests/test_api.py tests/test_autodetect.py tests/test_collector.py tests/test_database.py tests/test_main.py tests/test_network.py  # Multiple files
pytest tests/ -k "not test_database"              # All except database
```
```

### Coverage Configuration

Coverage settings are configured in `pytest.ini`:
- Minimum coverage: 80%
- Coverage reports: HTML, XML, and terminal
- Source code location: `src/netpulse/`

## Continuous Integration

Tests are designed to run in CI/CD environments and should:

- Be idempotent (can run multiple times safely)
- Not depend on external services unless marked
- Clean up after themselves
- Provide clear error messages on failure