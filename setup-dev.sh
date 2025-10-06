#!/bin/bash

# CarConnectivity Audi Connector - Development Environment Setup
# This script sets up the development environment with editable installs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Setting up CarConnectivity Audi Connector development environment..."
print_status "Working directory: $SCRIPT_DIR"

# Step 1: Create development virtual environment
print_status "Step 1: Setting up development virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    print_status "Creating development virtual environment..."
    python3 -m venv .venv
else
    print_status "Development virtual environment already exists"
fi

# Step 2: Install development dependencies
print_status "Step 2: Installing development dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install --upgrade "setuptools>=78.1.1"  # Security: Fix PYSEC-2022-43012, PYSEC-2025-49
.venv/bin/pip install build wheel pre-commit

# Step 2.1: Install security scanning tools
print_status "Step 2.1: Installing security scanning tools..."
.venv/bin/pip install pip-audit bandit safety

# Step 3: Install CarConnectivity and plugins
print_status "Step 3: Installing CarConnectivity framework and plugins..."
.venv/bin/pip install carconnectivity-cli carconnectivity-plugin-webui carconnectivity-plugin-mqtt

# Step 4: Install Audi connector in editable mode
print_status "Step 4: Installing Audi connector in editable mode..."
.venv/bin/pip install -e .

# Step 5: Set up pre-commit hooks
print_status "Step 5: Setting up pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    .venv/bin/pre-commit install
    print_success "Pre-commit hooks installed!"
else
    print_warning "No .pre-commit-config.yaml found - skipping pre-commit setup"
fi

print_success "Development environment setup complete!"
echo ""
print_status "=== DEVELOPMENT ENVIRONMENT READY ==="
echo ""
print_status "To activate the development environment:"
echo "  source .venv/bin/activate"
echo ""
print_status "To run the service in development mode:"
echo "  source .venv/bin/activate"
echo "  carconnectivity-cli audi_config.json"
echo ""
print_status "To test your changes:"
echo "  ./tools/1_build_and_test.sh  # Builds and tests in separate environment"
echo "  ./tools/2_run-test.sh        # Runs tests only"
echo ""
print_status "Security scanning commands:"
echo "  pip-audit --desc             # Check for vulnerable dependencies"
echo "  bandit -r src/               # Static security analysis"
echo "  safety check                 # Alternative vulnerability scanner"
echo ""
print_status "Development benefits:"
echo "  ✓ Editable install - changes to code are immediately available"
echo "  ✓ Full CarConnectivity setup with all plugins"
echo "  ✓ Security tools pre-installed (pip-audit, bandit, safety)"
echo "  ✓ Secure dependency versions (setuptools >=78.1.1)"
echo "  ✓ Separate from test environment"
echo ""
print_success "Happy coding! 🚗💻"
