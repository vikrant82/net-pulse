#!/usr/bin/env python3
"""
Net-Pulse: Lightweight network traffic monitoring application.

This is the main entry point for the Net-Pulse application.
"""

import uvicorn
from fastapi import FastAPI

from netpulse import __version__
from netpulse.database import initialize_database
from netpulse.network import get_network_interfaces, get_interface_stats, get_all_interface_stats, validate_interface, get_primary_interface
from netpulse.collector import get_collector, initialize_collector_config, CollectorError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Net-Pulse",
        description="Lightweight network traffic monitoring application",
        version=__version__,
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

    return app


def main() -> None:
    """Main entry point for the application."""
    # Initialize database on startup
    initialize_database()

    # Initialize collector configuration
    initialize_collector_config()

    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()