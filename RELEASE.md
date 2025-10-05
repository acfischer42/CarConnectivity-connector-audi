# Release Process

This document describes how to create and publish releases for the CarConnectivity Audi Connector.

## Prerequisites

1. **PyPI Trusted Publisher**: Already configured ✅
2. **GitHub repository**: Must have write access
3. **Clean working directory**: All changes committed
4. **Main branch**: Must be on main branch

## Automated Release Process

The release process is fully automated using GitHub Actions with PyPI Trusted Publisher:

### 1. Create a Release

Use the provided release script:

```bash
./release.sh
```

This will:
- Check that you're on the main branch
- Verify working directory is clean
- Prompt for the new version number
- Create and push a git tag
- Trigger the automated build and publish pipeline

### 2. Manual Tag Creation (Alternative)

If you prefer to create tags manually:

```bash
# Create and push tag
git tag v0.1.2
git push origin v0.1.2
```

### 3. GitHub Release (Optional)

Create a GitHub release with auto-generated notes:

```bash
gh release create v0.1.2 --generate-notes
```

## What Happens Automatically

When you push a version tag (e.g., `v0.1.2`), GitHub Actions will:

1. **Build Package**:
   - Set up Python environment
   - Install build dependencies
   - Build source distribution and wheel
   - Run package validation

2. **Publish to PyPI**:
   - Use PyPI Trusted Publisher (no tokens needed!)
   - Upload to https://pypi.org/project/carconnectivity-connector-audi/

3. **Create GitHub Release**:
   - Sign packages with Sigstore
   - Attach built packages to GitHub release
   - Generate release notes automatically

## Manual Testing

Test the package build before releasing:

```bash
# Build locally
python -m build

# Check package
python -m twine check dist/*

# Test installation
pip install dist/*.whl
```

## Versioning

We use semantic versioning (semver):
- `MAJOR.MINOR.PATCH` (e.g., `0.1.2`)
- Managed by `setuptools-scm` based on git tags
- Version automatically determined from git tags

## Monitoring

Monitor the release process:
- **GitHub Actions**: https://github.com/acfischer42/CarConnectivity-connector-audi/actions
- **PyPI Project**: https://pypi.org/project/carconnectivity-connector-audi/
- **GitHub Releases**: https://github.com/acfischer42/CarConnectivity-connector-audi/releases

## Troubleshooting

### Failed PyPI Upload
- Check PyPI Trusted Publisher configuration
- Verify GitHub repository settings
- Check Action logs for specific errors

### Version Conflicts
- Ensure version tags follow semver format
- Cannot republish same version to PyPI
- Use `git tag -d v0.1.2` to delete local tag if needed

### Build Failures
- Check Python version compatibility
- Verify all dependencies are available
- Review test-build.yml workflow for errors
