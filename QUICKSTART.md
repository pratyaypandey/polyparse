# Quick Start Guide for Maintainers

## Overview

Polyparse is now packaged as a distributable Python CLI tool with support for:
- PyPI distribution
- Homebrew installation
- Automated releases via GitHub Actions

## Files Added

### Packaging Files
- `pyproject.toml` - Modern Python packaging configuration
- `MANIFEST.in` - Controls what files are included in distributions
- `LICENSE` - MIT license (required for Homebrew)

### GitHub Workflows
- `.github/workflows/release.yml` - Automates releases when you push a git tag
- `.github/workflows/ci.yml` - Runs tests on PRs and pushes to main

### Homebrew Support
- `Formula/polyparse.rb` - Homebrew formula template
- `scripts/generate_formula.sh` - Script to generate formula after releases

### Documentation
- `DISTRIBUTION.md` - Comprehensive guide for distribution
- `RELEASE.md` - Step-by-step release checklist
- `QUICKSTART.md` - This file

## Quick Start

### 1. First Release

```bash
# Update version in polyparse/__init__.py and pyproject.toml
vim polyparse/__init__.py
vim pyproject.toml

# Commit and tag
git add .
git commit -m "Prepare release v0.1.0"
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin main
git push origin v0.1.0

# GitHub Actions will automatically:
# - Build the package
# - Create a GitHub release
# - Publish to PyPI (if PYPI_TOKEN is set)
```

### 2. Generate Homebrew Formula

```bash
# After the release is published on GitHub
./scripts/generate_formula.sh v0.1.0

# Test it locally
brew install --build-from-source ./Formula/polyparse.rb
polyparse --help
```

### 3. Create Homebrew Tap (Optional)

For easier distribution, create a tap repository:

```bash
# Create a new GitHub repository named: homebrew-polyparse
# Copy the formula there
mkdir -p homebrew-polyparse/Formula
cp Formula/polyparse.rb homebrew-polyparse/Formula/

# Users can then install with:
# brew tap yourusername/polyparse
# brew install polyparse
```

## Installation Methods

Once set up, users can install via:

```bash
# Homebrew (after tap setup)
brew tap yourusername/polyparse
brew install polyparse

# PyPI (after first release)
pip install polyparse

# Direct from source
git clone https://github.com/yourusername/polyparse.git
cd polyparse
pip install -e .
```

## Configuration Needed

### 1. Update GitHub Repository URLs

Search and replace `yourusername/polyparse` with your actual GitHub username/repo in:
- `pyproject.toml`
- `Formula/polyparse.rb`
- `scripts/generate_formula.sh`
- `README.md`
- `DISTRIBUTION.md`

### 2. Set Up PyPI Token (Optional)

For automatic PyPI publishing:
1. Create API token at https://pypi.org/manage/account/token/
2. Add to GitHub: Settings → Secrets → Actions → New secret
3. Name it `PYPI_TOKEN`

### 3. Update Author Information

Edit `pyproject.toml`:
- Update `authors` section with your name and email

## Testing Before Release

```bash
# Run tests
pytest

# Build locally
python -m build

# Install locally and test
pip install -e .
polyparse --help
```

## Common Tasks

### Update Dependencies

Edit `pyproject.toml` under `dependencies = [...]`

### Add Development Dependencies

Edit `pyproject.toml` under `[project.optional-dependencies]`

### Test Homebrew Formula

```bash
# After generating formula
brew install --build-from-source ./Formula/polyparse.rb
brew test polyparse
brew audit --strict polyparse
```

## Support

For issues or questions:
- Open an issue on GitHub
- See DISTRIBUTION.md for detailed documentation
- See RELEASE.md for release checklist
