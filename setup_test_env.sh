#!/bin/bash
# Net-Pulse Test Environment Setup Script
# This script sets up the virtual environment and installs all test dependencies

echo "🚀 Setting up Net-Pulse test environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python3 -m pip install --upgrade pip

# Install the project with test dependencies
echo "📥 Installing Net-Pulse with test dependencies..."
python3 -m pip install -e ".[test]"

# Verify installation
echo "✅ Verifying installation..."
python3 -c "import netpulse; print(f'✅ Net-Pulse {netpulse.__version__} installed successfully!')"
python3 -m pytest --version

echo ""
echo "🎉 Test environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "source venv/bin/activate"
echo ""
echo "To run tests:"
echo "python3 -m pytest tests/"
echo ""
echo "To run tests with coverage:"
echo "python3 -m pytest tests/ --cov=src/netpulse"