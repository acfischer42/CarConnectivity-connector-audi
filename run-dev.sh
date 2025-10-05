#!/bin/bash

# CarConnectivity Audi Connector - Development Run Script
# This script runs the service using the development environment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if development environment exists
if [ ! -d ".venv" ]; then
    print_error "Development environment not found."
    print_status "Please run ./setup-dev.sh first to set up the development environment"
    exit 1
fi

# Check if config exists
if [ ! -f "audi_config.json" ]; then
    print_error "Configuration file audi_config.json not found"
    print_status "Please create audi_config.json with your Audi credentials"
    exit 1
fi

# Check for port conflicts and suggest alternative
CONFIG_PORT=$(grep -o '"port"[[:space:]]*:[[:space:]]*[0-9]*' audi_config.json 2>/dev/null | grep -o '[0-9]*' || echo "4000")
DEFAULT_PORT=${CONFIG_PORT:-4000}

if command -v lsof &> /dev/null; then
    if lsof -i :$DEFAULT_PORT &>/dev/null; then
        print_warning "Port $DEFAULT_PORT is already in use"
        print_status "The service will automatically try to find an available port"
    fi
fi

print_status "Starting CarConnectivity Audi Connector (Development Mode)..."
print_status "Using development environment (.venv) with editable install"
print_status "Configuration file: audi_config.json"
print_status "Expected WebUI port: $DEFAULT_PORT"
print_success "Starting service (press Ctrl+C to stop)..."
echo ""

# Start the service using development environment
source .venv/bin/activate

# Open browser to WebUI (give service a moment to start)
print_status "Opening WebUI in browser at http://localhost:$DEFAULT_PORT (waiting 6 seconds for service to start)"
(
    sleep 6  # Give the service more time to start
    # Try different browser commands based on what's available
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:$DEFAULT_PORT" &>/dev/null &
    elif command -v firefox &> /dev/null; then
        firefox "http://localhost:$DEFAULT_PORT" &>/dev/null &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "http://localhost:$DEFAULT_PORT" &>/dev/null &
    elif command -v chromium &> /dev/null; then
        chromium "http://localhost:$DEFAULT_PORT" &>/dev/null &
    else
        print_warning "No browser found. Please manually open http://localhost:$DEFAULT_PORT"
    fi
) &

carconnectivity-cli audi_config_dev.json