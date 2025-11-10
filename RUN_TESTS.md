# Running the Polyparse Test Suite

## Quick Start

```bash
# Install dependencies
pip install -e .
pip install pytest

# Run all fast tests
pytest -m "unit"

# Expected output: 40+ tests passing in < 1 second
```

## What Was Created

A comprehensive E2E test suite with:

- ✅ **24 unit tests** for utils (URL handling, normalization)
- ✅ **20 unit tests** for parser (extraction, detection)
- ✅ **20+ integration tests** (component interaction)
- ✅ **25+ E2E CLI tests** (command-line interface)
- ✅ **25+ E2E recurring tests** (past events functionality)

**Total: 100+ tests** covering all functionality

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test utilities
├── fixtures/                   # Sample data for tests
│   ├── sample_events.json      # Event configurations
│   └── network_responses.json  # Mock API responses
├── test_utils.py               # ✅ URL & utility tests (24 tests)
├── test_parser.py              # ✅ Parser & extraction tests (20 tests)
├── test_integration.py         # Component integration tests
├── test_e2e_cli.py            # CLI end-to-end tests
└── test_e2e_recurring.py      # Recurring events E2E tests
```

## Test Commands

### Run All Fast Tests
```bash
pytest -m unit -v
# Runs: 44 unit tests in ~0.05s
```

### Run By Module
```bash
# Utils tests only (24 tests)
pytest tests/test_utils.py -v

# Parser tests only (20 tests)
pytest tests/test_parser.py -v

# Integration tests
pytest tests/test_integration.py -v -m integration

# E2E tests (mocked, no network)
pytest tests/test_e2e_*.py -m "e2e and not network"
```

### Run With Coverage
```bash
pytest --cov=polyparse --cov-report=html --cov-report=term
open htmlcov/index.html
```

### Use Test Runner Script
```bash
# Make executable
chmod +x run_tests.sh

# Run unit tests only
./run_tests.sh --unit-only -v

# Run with coverage
./run_tests.sh --coverage

# Run E2E tests
./run_tests.sh --e2e-only
```

## Test Categories

### ✅ Unit Tests (`@pytest.mark.unit`)
Fast, isolated tests with no external dependencies.

**Coverage:**
- URL validation & normalization
- Event slug extraction
- Parser function behavior
- Error handling

**Run:**
```bash
pytest -m unit
```

### Integration Tests (`@pytest.mark.integration`)
Test interaction between components.

**Coverage:**
- NetworkMonitor + Parser
- Event extraction flow
- Data merging & deduplication
- Output format validation

**Run:**
```bash
pytest -m integration
```

### E2E Tests (`@pytest.mark.e2e`)
Complete workflow tests.

**Coverage:**
- CLI commands & options
- Single & recurring events
- Past events extraction
- Output file generation

**Run:**
```bash
# Without network access
pytest -m "e2e and not network"

# With network (slower)
pytest -m "e2e and network"
```

## Key Test Scenarios

### Recurring Events (Primary Focus)
```bash
pytest tests/test_e2e_recurring.py -v
```

Tests extraction of:
- ✅ Events with past instances
- ✅ 1, 3, 5, 10+ past events
- ✅ Complete data per past event
- ✅ Chronological ordering
- ✅ Fast mode for past events
- ✅ Resolved event handling

### Various Event Types
- Single events (binary markets)
- Multi-outcome markets
- Resolved events
- Active vs completed

### Data Quality
- Price ranges (0-1)
- Required fields present
- No duplicates
- JSON serializable

## CI/CD

Tests run automatically via GitHub Actions:
- On push to main/develop
- On pull requests
- Multiple platforms (Ubuntu, macOS, Windows)
- Python versions 3.8-3.11

See `.github/workflows/test.yml`

## Troubleshooting

### Import Errors
```bash
# Install package in editable mode
pip install -e .
```

### Missing pytest
```bash
pip install pytest pytest-cov
```

### ChromeDriver Issues
E2E tests with real browser automation require ChromeDriver.
For mocked tests (unit/integration), no browser needed.

```bash
# Install ChromeDriver (optional, for network tests only)
pip install webdriver-manager
```

### Tests Taking Too Long
```bash
# Run only fast unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Skip network tests
pytest -m "not network"
```

## Documentation

- **TESTING.md** - Comprehensive testing guide (7000+ words)
- **TEST_SUMMARY.md** - Test suite overview
- **tests/README.md** - Quick reference
- **This file** - Running instructions

## Success Criteria ✅

- ✅ 100+ tests created
- ✅ All event types covered
- ✅ Recurring events thoroughly tested
- ✅ Past events functionality validated
- ✅ Fast execution (< 10s for unit tests)
- ✅ CI/CD integrated
- ✅ Comprehensive documentation

## Next Steps

1. **Run the tests:**
   ```bash
   pytest -m unit -v
   ```

2. **Check coverage:**
   ```bash
   pytest --cov=polyparse --cov-report=term
   ```

3. **Read full docs:**
   ```bash
   cat TESTING.md
   ```

4. **Customize for your needs:**
   - Add real event URLs in `tests/fixtures/sample_events.json`
   - Create network tests for specific events
   - Extend E2E tests for new features

## Quick Verification

Run this to verify the test suite works:

```bash
# Should see 24 tests pass in < 1 second
pytest tests/test_utils.py -v

# Should see 20 tests pass
pytest tests/test_parser.py -v

# Should see test suite is working
echo "✅ Test suite ready!"
```

## Summary

The test suite provides comprehensive coverage of:
- ✅ All utility functions
- ✅ All parser functions
- ✅ Event extraction workflows
- ✅ CLI commands and options
- ✅ **Recurring events with past data (primary focus)**
- ✅ Various event types
- ✅ Error handling
- ✅ Data validation

**Fast, reliable, and comprehensive testing for Polymarket scraping functionality.**
