#!/bin/bash
# Auto-release script for CarConnectivity Audi Connector
# Automatically increments patch version

set -e

# Get the project root directory (parent of tools directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

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

# Get current version and auto-increment patch
current_version=$(python3 -c "from src.carconnectivity_connectors.audi._version import __version__; print(__version__)")
echo "Current version: $current_version"

# Extract base version (remove .dev and everything after)
base_version=$(echo "$current_version" | sed 's/\.dev.*//g')

# Parse version parts
IFS='.' read -ra VERSION_PARTS <<< "$base_version"
major=${VERSION_PARTS[0]}
minor=${VERSION_PARTS[1]}  
patch=${VERSION_PARTS[2]}

# Auto-increment patch version
new_patch=$((patch + 1))
new_version="$major.$minor.$new_patch"

echo "Auto-generating new version: $new_version"

# Confirm with user
read -p "Create release v$new_version? [Y/n]: " confirm
if [[ $confirm =~ ^[Nn]$ ]]; then
    echo "Release cancelled"
    exit 0
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
    echo "🔗 Or create it via web interface at: https://github.com/acfischer42/CarConnectivity-connector-audi/releases/new"
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
    echo "📦 GitHub Actions will now build and publish to PyPI automatically."
    echo "🔗 Check the progress at: https://github.com/acfischer42/CarConnectivity-connector-audi/actions"
else
    echo "❌ Failed to create GitHub release. You can create it manually:"
    echo "   gh release create v$new_version --generate-notes"
    echo "🔗 Or via web interface at: https://github.com/acfischer42/CarConnectivity-connector-audi/releases/new"
fi
