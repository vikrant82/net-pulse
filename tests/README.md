# Net-Pulse Test Suite

This directory contains the comprehensive test suite for the Net-Pulse application.

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Pytest configuration and fixtures
├── README.md                # This file
├── test_collector.py        # **Core Polling Engine tests (73 tests)**
├── test_database.py         # Tests for database module (comprehensive CRUD operations)
├── test_main.py             # Tests for main application module
├── test_network.py          # Tests for network module (comprehensive interface testing)
├── test_init.py             # Tests for package initialization
├── test_utils.py            # Test utilities and helper functions
└── test_test_utils.py       # Tests for test utilities
```

### Test Module Overview

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

- **`test_main.py`** (15 tests) - Main application testing:
  - FastAPI application creation
  - API endpoints and routing
  - Application configuration

- **`test_utils.py`** - Utility functions and helpers
- **`test_test_utils.py`** - Testing utilities and fixtures
- **`test_init.py`** - Package initialization tests

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
pytest tests/test_collector.py     # Core Polling Engine tests (73 tests)
pytest tests/test_database.py      # Database module tests (45 tests)
pytest tests/test_main.py          # Main application tests (15 tests)
pytest tests/test_network.py       # Network module tests (80 tests)
pytest tests/test_utils.py         # Utility functions tests
pytest tests/test_init.py          # Package initialization tests

# Run multiple specific test files
pytest tests/test_collector.py tests/test_database.py tests/test_main.py tests/test_network.py tests/test_utils.py

# Run all tests except specific modules
pytest tests/ -k "not test_database"
```

### Run tests by module functionality
```bash
# Core Polling Engine tests only
pytest tests/test_collector.py

# Database-related tests only
pytest tests/test_database.py

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
pytest --cov=src/netpulse/collector --cov=src/netpulse/database --cov=src/netpulse/network --cov=src/netpulse/main --cov-report=html

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
pytest tests/test_collector.py -v         # Run collector tests only (73 tests)

# 📊 Coverage commands
pytest --cov=src/netpulse --cov-report=html --cov-report=term-missing
pytest --cov=src/netpulse --cov-fail-under=80

# 🧪 Module-specific tests
pytest tests/test_collector.py            # Core Polling Engine (73 tests)
pytest tests/test_database.py             # Database module (45 tests)
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
pytest tests/test_collector.py tests/test_database.py tests/test_main.py tests/test_network.py  # Multiple files
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