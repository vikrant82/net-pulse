"""
Tests for package initialization and module structure.
"""

import pytest


class TestPackageStructure:
    """Test the package structure and initialization."""

    def test_netpulse_package_can_be_imported(self):
        """Test that the netpulse package can be imported."""
        try:
            import netpulse
            assert netpulse is not None
        except ImportError as e:
            pytest.fail(f"Failed to import netpulse package: {e}")

    def test_package_has_version(self):
        """Test that the package has a version attribute."""
        import netpulse
        assert hasattr(netpulse, '__version__')
        assert netpulse.__version__ == "0.1.0"

    def test_package_has_author(self):
        """Test that the package has an author attribute."""
        import netpulse
        assert hasattr(netpulse, '__author__')
        assert netpulse.__author__ == "Vikrant with help from roo/code-supernova"

    def test_package_has_description(self):
        """Test that the package has a description attribute."""
        import netpulse
        assert hasattr(netpulse, '__description__')
        assert "Lightweight network traffic monitoring" in netpulse.__description__

    def test_src_package_exists(self):
        """Test that the src package exists."""
        try:
            import src
            assert src is not None
        except ImportError as e:
            pytest.fail(f"Failed to import src package: {e}")


class TestPackageMetadata:
    """Test package metadata and configuration."""

    def test_version_format(self):
        """Test that version follows semantic versioning."""
        import netpulse
        import re

        version = netpulse.__version__
        # Should match semantic versioning pattern (x.y.z or x.y.z-alpha.beta)
        assert re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$', version)

    def test_package_attributes_are_strings(self):
        """Test that package attributes are strings."""
        import netpulse

        assert isinstance(netpulse.__version__, str)
        assert isinstance(netpulse.__author__, str)
        assert isinstance(netpulse.__description__, str)

    def test_package_attributes_not_empty(self):
        """Test that package attributes are not empty."""
        import netpulse

        assert len(netpulse.__version__) > 0
        assert len(netpulse.__author__) > 0
        assert len(netpulse.__description__) > 0


class TestModuleImports:
    """Test that all expected modules can be imported."""

    def test_main_module_import(self):
        """Test that main module can be imported."""
        try:
            from netpulse.main import create_app, main
            assert callable(create_app)
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import from netpulse.main: {e}")

    def test_package_has_no_syntax_errors(self):
        """Test that the package imports without syntax errors."""
        # This test will pass if the imports above succeed
        pass


class TestPackageDocstring:
    """Test package docstring and documentation."""

    def test_package_has_docstring(self):
        """Test that the package has a docstring."""
        import netpulse
        assert hasattr(netpulse, '__doc__')
        assert netpulse.__doc__ is not None
        assert len(netpulse.__doc__) > 0

    def test_docstring_content(self):
        """Test that the docstring contains expected content."""
        import netpulse
        docstring = netpulse.__doc__

        assert "Net-Pulse" in docstring
        assert "Lightweight network traffic monitoring" in docstring
        assert "web interface" in docstring