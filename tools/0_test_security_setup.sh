#!/bin/bash

# Test Security and Code Quality Setup
# This script tests all the security and quality tools locally

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

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

print_header "Testing Security and Code Quality Setup"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Please run from the project root."
    exit 1
fi

# Install testing dependencies
print_header "Installing Test Dependencies"
print_status "Installing code quality tools..."
pip install --upgrade pip
pip install black==25.9.0 isort==6.1.0 flake8==7.3.0 mypy bandit safety pylint || {
    print_warning "Some tools failed to install. Continuing with available tools..."
}

# Ensure GitLeaks is installed (Go binary, not a pip package)
if ! command -v gitleaks &> /dev/null; then
    print_warning "GitLeaks not installed. Install with: go install github.com/gitleaks/gitleaks/v8@latest"
fi

# Test 1: Secret Detection
print_header "1. Testing Secret Detection"

print_status "Testing GitLeaks configuration..."
if command -v gitleaks &> /dev/null; then
    echo "Testing GitLeaks with current repository..."
    gitleaks detect --config .gitleaks.toml --verbose || {
        print_warning "GitLeaks found potential issues. Review the output above."
    }
    print_success "GitLeaks scan completed"
else
    print_warning "GitLeaks not installed. Install with: go install github.com/gitleaks/gitleaks/v8@latest"
fi

# Test 2: Code Formatting
print_header "2. Testing Code Formatting"

print_status "Testing Black formatting..."
if command -v black &> /dev/null; then
    echo "Checking code formatting (dry-run)..."
    black --check --diff src/ --extend-exclude '_version\.py' || {
        print_warning "Code formatting issues found. Run 'black src/' to fix."
    }
    print_success "Black formatting check completed"
else
    print_error "Black not installed"
fi

print_status "Testing import sorting..."
if command -v isort &> /dev/null; then
    echo "Checking import sorting (dry-run)..."
    isort --check-only --diff src/ --skip _version.py || {
        print_warning "Import sorting issues found. Run 'isort src/' to fix."
    }
    print_success "Import sorting check completed"
else
    print_error "isort not installed"
fi

# Test 3: Code Linting
print_header "3. Testing Code Linting"

print_status "Testing flake8 linting..."
if command -v flake8 &> /dev/null; then
    echo "Running flake8 linting..."
    flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics || {
        print_warning "Critical linting issues found"
    }
    flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    print_success "flake8 linting completed"
else
    print_error "flake8 not installed"
fi

print_status "Testing pylint analysis..."
if command -v pylint &> /dev/null; then
    echo "Running pylint analysis..."
    pylint src/carconnectivity_connectors/ --exit-zero --score=yes || true
    print_success "pylint analysis completed"
else
    print_error "pylint not installed"
fi

# Test 4: Type Checking
print_header "4. Testing Type Checking"

print_status "Testing mypy type checking..."
if command -v mypy &> /dev/null; then
    echo "Running mypy type checking..."
    mypy src/carconnectivity_connectors/ --ignore-missing-imports --no-strict-optional || {
        print_warning "Type checking issues found. Consider adding type hints."
    }
    print_success "mypy type checking completed"
else
    print_error "mypy not installed"
fi

# Test 5: Security Analysis
print_header "5. Testing Security Analysis"

print_status "Testing bandit security analysis..."
if command -v bandit &> /dev/null; then
    echo "Running bandit security scan..."
    bandit -r src/ -f txt || {
        print_warning "Security issues found. Review the output above."
    }
    print_success "bandit security scan completed"
else
    print_error "bandit not installed"
fi

print_status "Testing dependency vulnerability scan..."
if command -v safety &> /dev/null; then
    echo "Running safety dependency scan..."
    safety check || {
        print_warning "Vulnerable dependencies found. Review and update."
    }
    print_success "safety dependency scan completed"
else
    print_error "safety not installed"
fi

# Test 6: Pre-commit Hooks
print_header "6. Testing Pre-commit Hooks"

print_status "Testing pre-commit setup..."
if command -v pre-commit &> /dev/null; then
    if [ -f ".pre-commit-config.yaml" ]; then
        echo "Running pre-commit on all files..."
        pre-commit run --all-files || {
            print_warning "Pre-commit hooks found issues. Review and fix as needed."
        }
        print_success "Pre-commit hooks tested"
    else
        print_error ".pre-commit-config.yaml not found"
    fi
else
    print_error "pre-commit not installed. Install with: pip install pre-commit"
fi

# Test 7: Build Test
print_header "7. Testing Package Build"

print_status "Testing package build..."
if [ -f "pyproject.toml" ]; then
    echo "Building package..."
    python -m pip install --upgrade build
    python -m build || {
        print_error "Package build failed"
        exit 1
    }
    print_success "Package built successfully"

    print_status "Testing package installation..."
    pip install dist/*.whl --force-reinstall || {
        print_error "Package installation failed"
        exit 1
    }

    print_status "Testing package import..."
    python -c "import carconnectivity_connectors.audi; print('✓ Import successful')" || {
        print_error "Package import failed"
        exit 1
    }
    print_success "Package installation and import successful"
else
    print_error "pyproject.toml not found"
fi

# Test 8: Configuration Files
print_header "8. Testing Configuration Files"

print_status "Checking configuration files..."

configs=(
    ".github/workflows/security-and-quality.yml"
    ".gitleaks.toml"
    ".pre-commit-config.yaml"
    "pyproject.toml"
    "audi_config_template.json"
    "audi_config_minimal.json"
    "tools/1_build_and_test.sh"
)

for config in "${configs[@]}"; do
    if [ -f "$config" ]; then
        print_success "✓ $config exists"
    else
        print_error "✗ $config missing"
    fi
done

# Summary
print_header "Test Summary"

print_status "Local testing completed! Here's what to do next:"
echo ""
echo "🔧 To fix formatting issues:"
echo "   black src/"
echo "   isort src/"
echo ""
echo "🔍 To run security scans:"
echo "   gitleaks detect --config .gitleaks.toml"
echo "   bandit -r src/"
echo "   safety check"
echo ""
echo "⚙️  To run pre-commit on all files:"
echo "   pre-commit run --all-files"
echo ""
echo "🚀 To test GitHub Actions:"
echo "   git add ."
echo "   git commit -m 'test: security and quality setup'"
echo "   git push origin dev"
echo ""

print_success "All tests completed! Check the output above for any issues to fix."
