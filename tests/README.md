# Polyparse Test Suite

Comprehensive end-to-end and unit tests for the Polyparse Polymarket scraper.

## Quick Start

```bash
# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run fast tests only
pytest -m "unit"

# Run with coverage
pytest --cov=polyparse --cov-report=html
```

## Test Organization

- `test_utils.py` - Unit tests for URL handling and utilities
- `test_parser.py` - Unit tests for parsing and data extraction
- `test_integration.py` - Integration tests for component interaction
- `test_e2e_cli.py` - End-to-end CLI functionality tests
- `test_e2e_recurring.py` - End-to-end recurring events tests

## Test Markers

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests that take > 5 seconds
- `@pytest.mark.network` - Tests requiring network access
- `@pytest.mark.auth` - Tests requiring authentication

## Running Specific Tests

```bash
# Run only unit tests
pytest -m unit

# Run E2E tests without network
pytest -m "e2e and not network"

# Run a specific test file
pytest tests/test_utils.py -v

# Run a specific test
pytest tests/test_parser.py::TestPriceParsing::test_parse_percentage_format -v
```

## Coverage

View test coverage:

```bash
pytest --cov=polyparse --cov-report=term --cov-report=html
open htmlcov/index.html
```

## See Also

- [TESTING.md](../TESTING.md) - Comprehensive testing guide
- [README.md](../README.md) - Project documentation
