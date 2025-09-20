Here's the updated technical summary for **Project Net-Pulse**, incorporating the new psutil-based architecture.

## Project Net-Pulse: Technical Design Summary

### 1. Project Goal 🎯
To create a lightweight, self-hosted network traffic monitor for home labs. The application will automatically detect and monitor network interfaces, store traffic data, and provide an interactive web dashboard for visualization.

---

### 2. Architecture Overview
The system is composed of four main components designed to run within a single Docker container:

* **Collector Service**: A background scheduler that polls network interfaces using psutil.
* **Database**: An embedded **SQLite** database that stores both time-series traffic data and user configuration.
* **API Server**: A **FastAPI** backend that serves the collected data and the frontend application.
* **Web UI**: A browser-based dashboard for configuration and data visualization.

---

### 3. Technology Stack 🛠️
* **Backend**: **Python**
    * Web Framework: **FastAPI**
    * Scheduler: **apscheduler**
    * System Monitoring: **psutil** (cross-platform network interface detection and traffic monitoring)
    * Database: **sqlite3**
* **Frontend**: **Svelte**
    * Charting Library: **Chart.js**
* **Deployment**: **Docker** & **Docker Compose**

---

### 4. Key Features & Logic
* **Unified Network Monitoring with psutil**:
    * **Interface Discovery**: On startup, the application uses `psutil.net_if_addrs()` to enumerate all available network interfaces across **Linux, macOS, and Windows**.
    * **Default Gateway Detection**: Uses `psutil.net_if_addrs()` to identify the primary network interface by finding interfaces with default route configuration.
    * **Traffic Monitoring**: The collector uses `psutil.net_io_counters(pernic=True)` to get per-interface RX/TX byte counts, eliminating the need for external command execution.
    * **Delta Calculation**: The system calculates traffic deltas between polling intervals and handles counter resets (e.g., after system reboot) automatically.

* **Configuration UI**:
    * A **settings page** in the web UI will allow users to customize which network interfaces are monitored.
    * It will display a list of all available interfaces discovered by psutil and allow the user to **select one or more via checkboxes**.
    * The user's selection is saved in the SQLite database, ensuring it persists across application restarts.

* **API Endpoints**:
    * The backend provides endpoints to support the dynamic UI:
        * `GET /api/interfaces`: Lists all available network interfaces discovered by psutil.
        * `POST /api/config/monitored_interfaces`: Saves the user's selection of interfaces to the database.
        * `GET /api/traffic`: Fetches aggregated traffic data for the monitored interface(s) based on user-selected time windows and grouping intervals.

* **Interactive Dashboard**:
    * The main dashboard features a line chart displaying downloaded (RX) and uploaded (TX) traffic.
    * Users can use interactive sliders to dynamically adjust the **time window** and **data grouping** for the chart.

---

### 5. psutil Implementation Details

#### Network Interface Discovery
```python
import psutil

# Get all network interfaces
interfaces = psutil.net_if_addrs()
io_counters = psutil.net_io_counters(pernic=True)

# Filter for interfaces with traffic
active_interfaces = {
    name: stats for name, stats in io_counters.items()
    if name in interfaces
}
```

#### Traffic Data Collection
```python
import psutil
import time

def get_traffic_data():
    """Get current network I/O statistics for all interfaces."""
    return psutil.net_io_counters(pernic=True)

def calculate_deltas(current_stats, previous_stats):
    """Calculate traffic deltas between two measurement points."""
    deltas = {}
    for interface, current in current_stats.items():
        if interface in previous_stats:
            previous = previous_stats[interface]
            deltas[interface] = {
                'rx_bytes': current.bytes_recv - previous.bytes_recv,
                'tx_bytes': current.bytes_sent - previous.bytes_sent,
                'rx_packets': current.packets_recv - previous.packets_recv,
                'tx_packets': current.packets_sent - previous.packets_sent
            }
    return deltas
```

#### Counter Reset Handling
psutil automatically handles counter resets through its internal implementation, eliminating the need for custom reset detection logic.

---

### 6. Advantages of psutil Architecture

* **Simplified Dependencies**: Single library instead of multiple tools
* **Better Performance**: Direct kernel access vs. command parsing
* **Enhanced Reliability**: No external command dependencies
* **Cross-Platform Consistency**: Unified API across all supported platforms
* **Rich Statistics**: Access to additional metrics like packet counts, error rates
* **Future-Proof**: psutil is actively maintained and widely adopted

---

### 7. Migration Benefits

* **Reduced Complexity**: Eliminates command parsing and error handling
* **Better Error Handling**: psutil provides consistent error reporting
* **Enhanced Monitoring**: Access to additional network statistics
* **Improved Performance**: Faster data collection without process overhead
* **Simplified Deployment**: Fewer system dependencies to manage

This updated architecture using psutil provides a cleaner, more maintainable solution while delivering the same core functionality with improved reliability and performance.