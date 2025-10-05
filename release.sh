#!/bin/bash
# Release script for CarConnectivity Audi Connector

set -e

# Check if we're on main branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "Error: Must be on main branch to create a release. Currently on: $current_branch"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "Error: Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Run pre-commit checks to ensure code quality
echo "Running pre-commit checks..."
if command -v pre-commit &> /dev/null; then
    if ! pre-commit run --all-files; then
        echo "Error: Pre-commit checks failed. Please fix the issues and try again."
        echo "You can run 'pre-commit run --all-files' to see the specific failures."
        exit 1
    fi
    echo "✅ All pre-commit checks passed!"
else
    echo "Warning: pre-commit not found. Install with: pip install pre-commit"
    echo "Skipping code quality checks..."
fi

# Get current version
current_version=$(python3 -c "from src.carconnectivity_connectors.audi._version import __version__; print(__version__)")
echo "Current version: $current_version"

# Ask for new version
read -p "Enter new version (e.g., 0.1.2): " new_version

if [ -z "$new_version" ]; then
    echo "Error: Version cannot be empty"
    exit 1
fi

# Validate version format (basic check)
if ! [[ $new_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format x.y.z (e.g., 0.1.2)"
    exit 1
fi

echo "Creating release v$new_version..."

# Create and push tag
git tag "v$new_version"
git push origin "v$new_version"

echo "✅ Tag v$new_version created and pushed!"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) not found. Please install it with:"
    echo "   sudo apt install gh"
    echo "   gh auth login"
    echo ""
    echo "To create a GitHub release manually:"
    echo "   gh release create v$new_version --generate-notes"
    echo "� Or create it via web interface at: https://github.com/acfischer42/CarConnectivity-connector-audi/releases/new"
    exit 0
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo "⚠️  GitHub CLI not authenticated. Please run:"
    echo "   gh auth login"
    echo ""
    echo "To create a GitHub release manually:"
    echo "   gh release create v$new_version --generate-notes"
    exit 0
fi

# Create GitHub release
echo "🚀 Creating GitHub release..."
if gh release create "v$new_version" --generate-notes; then
    echo "✅ GitHub release v$new_version created successfully!"
    echo "�📦 GitHub Actions will now build and publish to PyPI automatically."
    echo "🔗 Check the progress at: https://github.com/acfischer42/CarConnectivity-connector-audi/actions"
else
    echo "❌ Failed to create GitHub release. You can create it manually:"
    echo "   gh release create v$new_version --generate-notes"
    echo "🔗 Or via web interface at: https://github.com/acfischer42/CarConnectivity-connector-audi/releases/new"
fi
