#!/usr/bin/env python3
"""
Net-Pulse: Lightweight network traffic monitoring application.

This is the main entry point for the Net-Pulse application.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import csv
import io
import logging
from datetime import datetime, timezone

from netpulse import __version__
from netpulse.database import initialize_database, get_traffic_data, get_database_stats, get_aggregated_traffic_data
from netpulse.network import (
    get_network_interfaces, get_interface_stats, get_all_interface_stats,
    validate_interface, get_primary_interface, get_interface_traffic_summary,
    NetworkError, InterfaceNotFoundError
)
from netpulse.collector import get_collector, initialize_collector_config, CollectorError
from netpulse.autodetect import initialize_auto_detection, AutoDetectionError

# Configure logging
logger = logging.getLogger(__name__)

# Pydantic models for API request/response validation
class InterfaceInfo(BaseModel):
    """Network interface information model."""
    name: str
    addresses: List[Dict[str, Any]]
    status: str
    mtu: Optional[int] = None
    speed: Optional[int] = None

class InterfaceStats(BaseModel):
    """Network interface statistics model."""
    interface_name: str
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    rx_errors: int
    tx_errors: int
    rx_drops: int
    tx_drops: int
    timestamp: str
    status: str

class TrafficDataRecord(BaseModel):
    """Traffic data record model."""
    id: int
    timestamp: str
    interface_name: str
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    created_at: str

class TrafficSummary(BaseModel):
    """Traffic summary model."""
    total_interfaces: int
    active_interfaces: int
    total_rx_bytes: int
    total_tx_bytes: int
    total_rx_packets: int
    total_tx_packets: int
    timestamp: str

class SystemInfo(BaseModel):
    """System information model."""
    hostname: str
    os: str
    python_version: str
    uptime_seconds: int
    cpu_count: int
    memory_total: int
    memory_available: int

class SystemHealth(BaseModel):
    """System health check model."""
    status: str
    database_status: str
    interfaces_status: str
    collector_status: str
    timestamp: str
    details: Dict[str, Any]

class SystemMetrics(BaseModel):
    """System performance metrics model."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_interfaces_count: int
    timestamp: str

class ConfigurationUpdate(BaseModel):
    """Configuration update model."""
    interfaces: Optional[List[str]] = None
    collection_interval: Optional[int] = Field(None, ge=1, le=3600)


class MaxRetriesUpdate(BaseModel):
    """Max retries configuration update model."""
    max_retries: int = Field(..., ge=1, le=100, description="Maximum retry attempts (1-100)")

class RetryDelayUpdate(BaseModel):
    """Retry delay configuration update model."""
    retry_delay: float = Field(..., gt=0, le=300, description="Delay between retries in seconds (0.1-300)")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    timestamp: str
    path: Optional[str] = None


# Create the FastAPI app instance at module level
app = FastAPI(
    title="Net-Pulse",
    description="Lightweight network traffic monitoring application",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Global exception handlers
@app.exception_handler(NetworkError)
async def network_error_handler(request, exc: NetworkError):
    logger.error(f"Network error: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "NetworkError",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(InterfaceNotFoundError)
async def interface_not_found_handler(request, exc: InterfaceNotFoundError):
    logger.warning(f"Interface not found: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
            "error": "InterfaceNotFoundError",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(CollectorError)
async def collector_error_handler(request, exc: CollectorError):
    logger.error(f"Collector error: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "CollectorError",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    from fastapi.responses import JSONResponse
    # Use FastAPI's default error format for consistency with tests
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url)
        }
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Net-Pulse",
        "version": __version__,
        "description": "Lightweight network traffic monitoring application",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/collector/status")
async def get_collector_status():
    """Get collector status and statistics."""
    try:
        collector = get_collector()
        return collector.get_collection_status()
    except CollectorError as e:
        return {"error": str(e), "status": "error"}

@app.post("/collector/start")
async def start_collector():
    """Start the network data collector."""
    try:
        collector = get_collector()
        collector.start_collection()
        return {"message": "Collector started successfully", "status": "running"}
    except CollectorError as e:
        return {"error": str(e), "status": "error"}

@app.post("/collector/stop")
async def stop_collector():
    """Stop the network data collector."""
    try:
        collector = get_collector()
        collector.stop_collection()
        return {"message": "Collector stopped successfully", "status": "stopped"}
    except CollectorError as e:
        return {"error": str(e), "status": "error"}

@app.post("/collector/collect")
async def manual_collection():
    """Trigger a manual collection cycle."""
    try:
        collector = get_collector()
        result = collector.collect_once()
        return result
    except CollectorError as e:
        return {"error": str(e), "status": "error"}

# ============================================================================
# INTERFACE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/interfaces",
          response_model=Dict[str, InterfaceInfo],
          summary="List all network interfaces",
          description="Get information about all available network interfaces including their addresses, status, and configuration.")
async def get_interfaces():
    """Get all network interfaces with their details."""
    try:
        logger.info("Fetching all network interfaces")
        interfaces = get_network_interfaces()
        return interfaces
    except NetworkError as e:
        logger.error(f"Failed to get network interfaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve network interfaces: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting interfaces: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/interfaces/{interface_name}",
          response_model=InterfaceInfo,
          summary="Get specific interface details",
          description="Get detailed information about a specific network interface including addresses and configuration.")
async def get_interface(
    interface_name: str = Path(..., description="Name of the network interface")
):
    """Get detailed information about a specific interface."""
    try:
        logger.info(f"Fetching details for interface: {interface_name}")
        interfaces = get_network_interfaces()

        if interface_name not in interfaces:
            raise HTTPException(
                status_code=404,
                detail=f"Interface '{interface_name}' not found"
            )

        return interfaces[interface_name]
    except HTTPException:
        raise
    except NetworkError as e:
        logger.error(f"Failed to get interface {interface_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve interface: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting interface {interface_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/interfaces/{interface_name}/stats",
          response_model=InterfaceStats,
          summary="Get interface traffic statistics",
          description="Get current traffic statistics for a specific network interface including bytes and packets sent/received.")
async def get_interface_stats_endpoint(
    interface_name: str = Path(..., description="Name of the network interface")
):
    """Get current traffic statistics for a specific interface."""
    try:
        logger.info(f"Fetching stats for interface: {interface_name}")
        stats = get_interface_stats(interface_name)
        return stats
    except InterfaceNotFoundError as e:
        logger.warning(f"Interface not found: {interface_name}")
        raise HTTPException(status_code=404, detail=str(e))
    except NetworkError as e:
        logger.error(f"Failed to get stats for interface {interface_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve interface statistics: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting interface stats {interface_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================================================
# TRAFFIC DATA ENDPOINTS
# ============================================================================

@app.get("/api/traffic/history",
          response_model=List[TrafficDataRecord],
          summary="Get historical traffic data",
          description="Retrieve historical traffic data with optional filtering by interface, time range, and pagination.")
async def get_traffic_history(
    interface_name: Optional[str] = Query(None, description="Filter by specific interface name"),
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of records to skip")
):
    """Get historical traffic data with optional filtering."""
    try:
        logger.info(f"Fetching traffic history: interface={interface_name}, limit={limit}, offset={offset}")
        traffic_data = get_traffic_data(
            limit=limit,
            offset=offset,
            interface_name=interface_name,
            start_time=start_time,
            end_time=end_time
        )
        return traffic_data
    except Exception as e:
        logger.error(f"Failed to get traffic history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve traffic data: {str(e)}")

@app.get("/api/traffic/summary",
          response_model=TrafficSummary,
          summary="Get traffic summary",
          description="Get a summary of all network traffic across all interfaces including totals and active interface count.")
async def get_traffic_summary():
    """Get traffic summary across all interfaces."""
    try:
        logger.info("Fetching traffic summary")
        summary = get_interface_traffic_summary()
        return summary
    except NetworkError as e:
        logger.error(f"Failed to get traffic summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve traffic summary: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting traffic summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/traffic/latest",
           response_model=List[TrafficDataRecord],
           summary="Get latest traffic data",
           description="Get the most recent traffic data records from the database.")
async def get_latest_traffic(
    limit: Optional[int] = Query(10, ge=1, le=100, description="Maximum number of records to return")
):
    """Get the most recent traffic data."""
    try:
        logger.info(f"Fetching latest traffic data: limit={limit}")
        traffic_data = get_traffic_data(limit=limit)
        return traffic_data
    except Exception as e:
        logger.error(f"Failed to get latest traffic data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest traffic data: {str(e)}")

@app.get("/api/traffic/history/aggregated",
           response_model=List[TrafficDataRecord],
           summary="Get aggregated traffic data",
           description="Get traffic data aggregated into exactly N data points for efficient chart display. Uses SQL aggregation for better performance.")
async def get_aggregated_traffic_history(
    start_time: str = Query("24h", description="Time window: 1h, 6h, 24h, 7d, 30d"),
    data_points: int = Query(50, ge=10, le=200, description="Number of aggregated data points to return"),
    interface_name: Optional[str] = Query(None, description="Filter by specific interface name")
):
    """Get aggregated traffic data with exactly N data points."""
    try:
        logger.info(f"Fetching aggregated traffic data: start_time={start_time}, data_points={data_points}, interface={interface_name}")

        # Get aggregated data from database
        aggregated_data = get_aggregated_traffic_data(
            start_time=start_time,
            data_points=data_points,
            interface_name=interface_name
        )

        # Convert to API response format
        response_data = []
        for record in aggregated_data:
            response_data.append({
                "id": None,  # Aggregated data doesn't have individual IDs
                "timestamp": record["timestamp"],
                "interface_name": record["interface_name"],
                "rx_bytes": record["rx_bytes"],
                "tx_bytes": record["tx_bytes"],
                "rx_packets": record["rx_packets"],
                "tx_packets": record["tx_packets"],
                "created_at": record["timestamp"]  # Use same timestamp for created_at
            })

        logger.info(f"Returning {len(response_data)} aggregated data points")
        return response_data

    except Exception as e:
        logger.error(f"Failed to get aggregated traffic data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve aggregated traffic data: {str(e)}")

# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@app.get("/api/config/interfaces",
          response_model=Dict[str, List[str]],
          summary="Get monitored interfaces",
          description="Get the list of network interfaces currently being monitored by the collector.")
async def get_monitored_interfaces():
    """Get list of monitored interfaces."""
    try:
        logger.info("Fetching monitored interfaces configuration")
        from netpulse.collector import get_collector
        collector = get_collector()
        monitored_interfaces = collector._get_monitored_interfaces()
        return {"interfaces": monitored_interfaces}
    except Exception as e:
        logger.error(f"Failed to get monitored interfaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve monitored interfaces: {str(e)}")

@app.put("/api/config/interfaces",
            response_model=Dict[str, Any],
            summary="Update monitored interfaces",
            description="Update the list of network interfaces to be monitored by the collector.")
async def update_monitored_interfaces(
    config: ConfigurationUpdate
):
    """Update monitored interfaces configuration."""
    try:
        logger.info(f"Updating monitored interfaces: {config.interfaces}")
        if config.interfaces is None:
            raise HTTPException(status_code=400, detail="interfaces field is required")

        # Validate interfaces exist
        invalid_interfaces = []
        for interface_name in config.interfaces:
            if not validate_interface(interface_name):
                invalid_interfaces.append(interface_name)

        if invalid_interfaces:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interfaces: {', '.join(invalid_interfaces)}"
            )

        # Update configuration
        from netpulse.database import set_configuration_value
        interfaces_str = ','.join(config.interfaces)
        set_configuration_value('collector.monitored_interfaces', interfaces_str)

        return {"message": "Monitored interfaces updated successfully", "interfaces": config.interfaces}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update monitored interfaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update monitored interfaces: {str(e)}")

@app.get("/api/config/collection-interval",
          response_model=Dict[str, int],
          summary="Get collection interval",
          description="Get the current data collection interval in seconds.")
async def get_collection_interval():
    """Get current collection interval."""
    try:
        logger.info("Fetching collection interval configuration")
        from netpulse.database import get_configuration_value
        interval_str = get_configuration_value('collector.polling_interval')
        interval = int(interval_str) if interval_str else 30
        return {"collection_interval_seconds": interval}
    except Exception as e:
        logger.error(f"Failed to get collection interval: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve collection interval: {str(e)}")

@app.put("/api/config/collection-interval",
          response_model=Dict[str, int],
          summary="Update collection interval",
          description="Update the data collection interval in seconds (1-3600).")
async def update_collection_interval(
    config: ConfigurationUpdate
):
    """Update collection interval configuration."""
    try:
        logger.info(f"Updating collection interval: {config.collection_interval}")
        if config.collection_interval is None:
            raise HTTPException(status_code=400, detail="collection_interval field is required")

        if not (1 <= config.collection_interval <= 3600):
            raise HTTPException(
                status_code=400,
                detail="Collection interval must be between 1 and 3600 seconds"
            )

        # Update configuration
        from netpulse.database import set_configuration_value
        set_configuration_value('collector.polling_interval', str(config.collection_interval))

        return {"collection_interval_seconds": config.collection_interval}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update collection interval: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update collection interval: {str(e)}")

@app.get("/api/config/max-retries",
          response_model=Dict[str, int],
          summary="Get max retries setting",
          description="Get the current maximum retry attempts setting.")
async def get_max_retries():
    """Get current max retries setting."""
    try:
        logger.info("Fetching max retries configuration")
        from netpulse.database import get_configuration_value
        retries_str = get_configuration_value('collector.max_retries')
        retries = int(retries_str) if retries_str else 3
        return {"max_retries": retries}
    except Exception as e:
        logger.error(f"Failed to get max retries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve max retries setting: {str(e)}")

@app.put("/api/config/max-retries",
          response_model=Dict[str, int],
          summary="Update max retries setting",
          description="Update the maximum retry attempts setting (1-100).")
async def update_max_retries(
    config: MaxRetriesUpdate
):
    """Update max retries configuration."""
    try:
        logger.info(f"Updating max retries: {config.max_retries}")
        if config.max_retries is None:
            raise HTTPException(status_code=400, detail="max_retries field is required")

        if not (1 <= config.max_retries <= 100):
            raise HTTPException(
                status_code=400,
                detail="Max retries must be between 1 and 100"
            )

        # Update configuration
        from netpulse.database import set_configuration_value
        set_configuration_value('collector.max_retries', str(config.max_retries))

        return {"max_retries": config.max_retries}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update max retries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update max retries setting: {str(e)}")

@app.get("/api/config/retry-delay",
          response_model=Dict[str, float],
          summary="Get retry delay setting",
          description="Get the current retry delay setting in seconds.")
async def get_retry_delay():
    """Get current retry delay setting."""
    try:
        logger.info("Fetching retry delay configuration")
        from netpulse.database import get_configuration_value
        delay_str = get_configuration_value('collector.retry_delay')
        delay = float(delay_str) if delay_str else 1.0
        return {"retry_delay_seconds": delay}
    except Exception as e:
        logger.error(f"Failed to get retry delay: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve retry delay setting: {str(e)}")

@app.put("/api/config/retry-delay",
          response_model=Dict[str, float],
          summary="Update retry delay setting",
          description="Update the retry delay setting in seconds (0.1-300).")
async def update_retry_delay(
    config: RetryDelayUpdate
):
    """Update retry delay configuration."""
    try:
        logger.info(f"Updating retry delay: {config.retry_delay}")
        if config.retry_delay is None:
            raise HTTPException(status_code=400, detail="retry_delay field is required")

        if not (0.1 <= config.retry_delay <= 300):
            raise HTTPException(
                status_code=400,
                detail="Retry delay must be between 0.1 and 300 seconds"
            )

        # Update configuration
        from netpulse.database import set_configuration_value
        set_configuration_value('collector.retry_delay', str(config.retry_delay))

        return {"retry_delay_seconds": config.retry_delay}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update retry delay: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update retry delay setting: {str(e)}")

# ============================================================================
# SYSTEM INFORMATION ENDPOINTS
# ============================================================================

@app.get("/api/system/info",
          response_model=SystemInfo,
          summary="Get system information",
          description="Get basic system information including hostname, OS, Python version, and hardware details.")
async def get_system_info():
    """Get system information."""
    try:
        logger.info("Fetching system information")
        import platform
        import psutil
        import socket

        info = {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
            "uptime_seconds": int(psutil.boot_time()),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available
        }
        return info
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system information: {str(e)}")

@app.get("/api/system/health",
          response_model=SystemHealth,
          summary="Get system health check",
          description="Perform a comprehensive health check of all system components including database, interfaces, and collector.")
async def get_system_health():
    """Get detailed system health check."""
    try:
        logger.info("Performing system health check")
        import platform
        import psutil
        import socket
        from datetime import datetime, timezone

        # Check database status
        db_status = "healthy"
        db_details = {}
        try:
            db_stats = get_database_stats()
            db_details = db_stats
        except Exception as e:
            db_status = "unhealthy"
            db_details = {"error": str(e)}

        # Check interfaces status
        interfaces_status = "healthy"
        interfaces_details = {}
        try:
            interfaces = get_network_interfaces()
            interfaces_details = {
                "total_interfaces": len(interfaces),
                "active_interfaces": sum(1 for iface in interfaces.values() if iface.get('status') == 'up')
            }
        except Exception as e:
            interfaces_status = "unhealthy"
            interfaces_details = {"error": str(e)}

        # Check collector status
        collector_status = "unknown"
        collector_details = {}
        try:
            collector = get_collector()
            collector_info = collector.get_collection_status()
            collector_status = "healthy" if collector_info.get('is_running', False) else "stopped"
            collector_details = collector_info
        except Exception as e:
            collector_status = "unhealthy"
            collector_details = {"error": str(e)}

        # Overall status
        overall_status = "healthy"
        if db_status == "unhealthy" or interfaces_status == "unhealthy" or collector_status == "unhealthy":
            overall_status = "unhealthy"
        elif collector_status == "stopped":
            overall_status = "degraded"

        health = {
            "status": overall_status,
            "database_status": db_status,
            "interfaces_status": interfaces_status,
            "collector_status": collector_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "database": db_details,
                "interfaces": interfaces_details,
                "collector": collector_details
            }
        }
        return health
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")

@app.get("/api/system/metrics",
          response_model=SystemMetrics,
          summary="Get system performance metrics",
          description="Get current system performance metrics including CPU, memory, disk usage, and network interface count.")
async def get_system_metrics():
    """Get system performance metrics."""
    try:
        logger.info("Fetching system metrics")
        import psutil
        import shutil
        from datetime import datetime, timezone

        # Get disk usage for the current directory
        disk_usage = shutil.disk_usage(".")

        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": (disk_usage.used / disk_usage.total) * 100,
            "network_interfaces_count": len(get_network_interfaces()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return metrics
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system metrics: {str(e)}")

# ============================================================================
# DATA EXPORT ENDPOINTS
# ============================================================================

@app.get("/api/export/traffic",
          summary="Export traffic data",
          description="Export traffic data in various formats (JSON, CSV) with optional filtering.")
async def export_traffic_data(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
    interface_name: Optional[str] = Query(None, description="Filter by specific interface name"),
    start_time: Optional[str] = Query(None, description="Start time filter (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time filter (ISO format)"),
    limit: Optional[int] = Query(1000, ge=1, le=10000, description="Maximum number of records to export")
):
    """Export traffic data in JSON or CSV format."""
    try:
        logger.info(f"Exporting traffic data: format={format}, interface={interface_name}, limit={limit}")

        # Get traffic data
        traffic_data = get_traffic_data(
            limit=limit,
            interface_name=interface_name,
            start_time=start_time,
            end_time=end_time
        )

        if format.lower() == "csv":
            # Create CSV response
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'id', 'timestamp', 'interface_name', 'rx_bytes', 'tx_bytes',
                'rx_packets', 'tx_packets', 'created_at'
            ])
            writer.writeheader()
            for record in traffic_data:
                writer.writerow(record)

            output.seek(0)
            return StreamingResponse(
                io.StringIO(output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=traffic_data.csv"}
            )
        else:
            # JSON response
            return traffic_data

    except Exception as e:
        logger.error(f"Failed to export traffic data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export traffic data: {str(e)}")


def main() -> None:
    """Main entry point for the application."""
    # Initialize database on startup
    initialize_database()

    # Initialize collector configuration
    initialize_collector_config()

    # Initialize auto-detection (optional, non-blocking)
    try:
        autodetect_result = initialize_auto_detection()
        print(f"Auto-detection status: {autodetect_result.get('status', 'unknown')}")
        if autodetect_result.get('status') == 'success':
            print(f"Auto-detection completed: {autodetect_result.get('details', {}).get('configured_interfaces', 0)} interfaces configured")
        elif autodetect_result.get('status') == 'already_initialized':
            print("Auto-detection was already performed on previous startup")
    except AutoDetectionError as e:
        print(f"Auto-detection failed (continuing anyway): {e}")
    except Exception as e:
        print(f"Unexpected error during auto-detection (continuing anyway): {e}")

    # The app is already created at module level
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()