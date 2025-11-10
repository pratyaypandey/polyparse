# Distribution Guide

This guide explains how to distribute Polyparse via Homebrew and PyPI.

## Prerequisites

1. GitHub repository with releases enabled
2. PyPI account and API token (optional, for PyPI distribution)
3. Homebrew tap repository (for Homebrew distribution)

## Releasing a New Version

### 1. Update Version

Update the version in these files:
- `polyparse/__init__.py`
- `pyproject.toml`

### 2. Create a Git Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 3. GitHub Release

The GitHub Actions workflow will automatically:
- Build the Python package
- Create a GitHub release
- Upload distribution files
- Publish to PyPI (if PYPI_TOKEN is configured)

### 4. Generate Homebrew Formula

After the release is published, generate the Homebrew formula:

```bash
./scripts/generate_formula.sh v0.1.0
```

This will:
- Download the release tarball
- Calculate the SHA256 checksum
- Generate an updated Formula/polyparse.rb

## Setting Up Homebrew Distribution

### Option 1: Homebrew Core (Recommended for Popular Tools)

Submit a pull request to [Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core):

1. Fork the repository
2. Copy your formula to `Formula/p/polyparse.rb`
3. Test the formula locally
4. Submit a PR

Requirements:
- 75+ stars on GitHub or notable popularity
- Open source license
- Stable release
- Active maintenance

### Option 2: Custom Tap (Easier for Getting Started)

Create your own Homebrew tap:

```bash
# Create a new repository named homebrew-polyparse
# Repository must be named homebrew-<tapname>

# Add the formula to the repository
mkdir -p Formula
cp Formula/polyparse.rb homebrew-polyparse/Formula/

# Users can then install with:
brew tap yourusername/polyparse
brew install polyparse
```

## Testing the Formula Locally

Before distributing, test your formula:

```bash
# Install from local formula
brew install --build-from-source ./Formula/polyparse.rb

# Test the installation
polyparse --help

# Audit the formula
brew audit --strict --online polyparse

# Uninstall
brew uninstall polyparse
```

## PyPI Distribution

The release workflow automatically publishes to PyPI if you set up the token:

1. Create a PyPI API token at https://pypi.org/manage/account/token/
2. Add it to GitHub Secrets as `PYPI_TOKEN`
3. The workflow will automatically publish on new releases

Manual PyPI publishing:

```bash
# Build the package
python -m build

# Upload to PyPI
twine upload dist/*
```

## Installation Methods After Setup

### Via Homebrew (macOS/Linux)

```bash
# If in Homebrew core
brew install polyparse

# If using custom tap
brew tap yourusername/polyparse
brew install polyparse
```

### Via PyPI

```bash
pip install polyparse
```

### Via GitHub Releases

```bash
# Download and install from release
curl -L https://github.com/yourusername/polyparse/archive/refs/tags/v0.1.0.tar.gz | tar xz
cd polyparse-0.1.0
pip install .
```

## Troubleshooting

### Homebrew Formula Issues

1. **SHA256 mismatch**: Regenerate the formula with the script
2. **Python version conflicts**: Update `depends_on "python@X.Y"` in formula
3. **Missing dependencies**: Add system dependencies to `depends_on`

### Building Issues

1. Check that all tests pass: `pytest`
2. Verify the package builds: `python -m build`
3. Test in a clean virtualenv

## Continuous Maintenance

1. Keep dependencies updated in `pyproject.toml`
2. Test on multiple Python versions (CI does this automatically)
3. Update Homebrew formula for each release
4. Monitor GitHub issues and respond to user feedback
