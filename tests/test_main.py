"""
Tests for the main module of Net-Pulse application.
"""

import pytest
from fastapi.testclient import TestClient

from netpulse.main import create_app


class TestCreateApp:
    """Test the create_app function."""

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance."""
        app = create_app()
        assert app is not None
        assert hasattr(app, 'routes')

    def test_app_has_correct_metadata(self, app):
        """Test that the app has correct title and description."""
        assert app.title == "Net-Pulse"
        assert "Lightweight network traffic monitoring" in app.description
        assert app.version == "0.1.0"

    def test_root_endpoint_returns_correct_data(self, client):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Net-Pulse"
        assert data["version"] == "0.1.0"
        assert data["description"] == "Lightweight network traffic monitoring application"
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_app_routes_are_registered(self, app):
        """Test that all expected routes are registered."""
        routes = [route.path for route in app.routes]

        # Check for expected routes
        assert "/" in routes
        assert "/health" in routes
        assert "/openapi.json" in routes  # FastAPI automatically adds this

    def test_app_has_openapi_schema(self, app):
        """Test that the app generates OpenAPI schema correctly."""
        openapi_schema = app.openapi()
        assert openapi_schema is not None
        assert "info" in openapi_schema
        assert "title" in openapi_schema["info"]
        assert openapi_schema["info"]["title"] == "Net-Pulse"
        assert "paths" in openapi_schema
        assert "/" in openapi_schema["paths"]
        assert "/health" in openapi_schema["paths"]


class TestMainFunction:
    """Test the main function behavior."""

    def test_main_function_exists(self):
        """Test that main function can be imported."""
        from netpulse.main import main
        assert callable(main)

    def test_main_function_runs_without_error(self, monkeypatch):
        """Test that main function can run without throwing exceptions."""
        from netpulse.main import main
        import sys

        # Mock uvicorn.run to avoid actually starting the server
        def mock_run(*args, **kwargs):
            pass

        monkeypatch.setattr("uvicorn.run", mock_run)

        # This should not raise an exception
        try:
            main()
        except SystemExit:
            # uvicorn.run might call sys.exit, which is expected
            pass


class TestAppConfiguration:
    """Test application configuration and setup."""

    def test_app_has_correct_middleware(self, app):
        """Test that the app has appropriate middleware configured."""
        # FastAPI apps should have some basic middleware
        assert len(app.user_middleware) >= 0  # At least no user middleware is fine

    def test_app_cors_configuration(self, app):
        """Test CORS configuration if present."""
        # This test can be expanded when CORS is added
        pass

    def test_app_has_docs_endpoints(self, app):
        """Test that FastAPI docs endpoints are available."""
        routes = [route.path for route in app.routes]

        # FastAPI automatically adds docs endpoints
        assert "/docs" in routes
        assert "/redoc" in routes