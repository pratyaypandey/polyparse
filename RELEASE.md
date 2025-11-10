# Release Checklist

Follow these steps to create a new release:

## Pre-release

- [ ] All tests pass: `pytest`
- [ ] Code is properly formatted: `black polyparse tests`
- [ ] Version is updated in:
  - [ ] `polyparse/__init__.py`
  - [ ] `pyproject.toml`
- [ ] CHANGELOG updated (if you maintain one)
- [ ] All changes committed to main branch

## Create Release

```bash
# 1. Create and push tag
VERSION="0.1.0"
git tag -a "v${VERSION}" -m "Release version ${VERSION}"
git push origin "v${VERSION}"

# 2. GitHub Actions will automatically:
#    - Build the package
#    - Create GitHub release
#    - Publish to PyPI (if configured)

# 3. Wait for the release workflow to complete
# Check: https://github.com/yourusername/polyparse/actions
```

## Update Homebrew Formula

```bash
# After GitHub release is published
./scripts/generate_formula.sh "v${VERSION}"

# Review the generated formula
cat Formula/polyparse.rb

# Test locally
brew install --build-from-source ./Formula/polyparse.rb
polyparse --help
brew uninstall polyparse

# If using custom tap, push to tap repository
cd ../homebrew-polyparse  # Your tap repository
cp ../polyparse/Formula/polyparse.rb Formula/
git add Formula/polyparse.rb
git commit -m "Update polyparse to ${VERSION}"
git push

# If submitting to Homebrew core, create PR to Homebrew/homebrew-core
```

## Post-release

- [ ] Test installation via Homebrew: `brew install polyparse`
- [ ] Test installation via PyPI: `pip install polyparse`
- [ ] Announce release (optional)
- [ ] Close related GitHub issues

## GitHub Secrets Configuration

For automatic PyPI publishing, add these secrets to your repository:

1. Go to: Settings → Secrets and variables → Actions
2. Add: `PYPI_TOKEN` with your PyPI API token

## Troubleshooting

### Release workflow fails

- Check GitHub Actions logs
- Verify all tests pass locally
- Ensure version numbers are correct

### Homebrew formula issues

- Verify the tarball URL is accessible
- Check SHA256 matches: `shasum -a 256 <downloaded-tarball>`
- Test formula syntax: `brew audit --strict ./Formula/polyparse.rb`

### PyPI upload fails

- Verify `PYPI_TOKEN` is set correctly
- Check if version already exists on PyPI
- Ensure package builds successfully: `python -m build`
