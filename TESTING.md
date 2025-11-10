# Polyparse Testing Guide

This document provides comprehensive information about testing the Polyparse application.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing Tests](#writing-tests)
6. [CI/CD Integration](#cicd-integration)
7. [Troubleshooting](#troubleshooting)

## Test Structure

The test suite is organized into the following structure:

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── fixtures/                   # Test data fixtures
│   ├── sample_events.json      # Sample event configurations
│   └── network_responses.json  # Mock network responses
├── test_utils.py               # Unit tests for utils module
├── test_parser.py              # Unit tests for parser module
├── test_integration.py         # Integration tests
├── test_e2e_cli.py            # End-to-end CLI tests
└── test_e2e_recurring.py      # End-to-end recurring events tests
```

## Test Categories

Tests are organized using pytest markers:

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and methods in isolation
- Fast execution (< 1 second per test)
- No external dependencies (network, browser, etc.)
- Mock all external interactions

**Coverage:**
- URL validation and normalization (`test_utils.py`)
- Price parsing and formatting (`test_parser.py`)
- Data structure validation
- Text extraction logic

### Integration Tests (`@pytest.mark.integration`)
- Test interaction between multiple components
- Mock external services but test real module interactions
- Test data flow through the system

**Coverage:**
- NetworkMonitor lifecycle
- Event extraction with network data
- Data deduplication and merging
- Output format validation

### End-to-End Tests (`@pytest.mark.e2e`)
- Test complete workflows from CLI to output
- May use mock or real browser automation
- Test the full application stack

**Coverage:**
- CLI command execution
- Event extraction workflows
- Recurring events extraction
- Output file generation

### Additional Markers

- `@pytest.mark.slow` - Tests that take > 5 seconds
- `@pytest.mark.network` - Tests requiring network access
- `@pytest.mark.auth` - Tests requiring authentication

## Running Tests

### Prerequisites

Install development dependencies:

```bash
pip install -e .
pip install -r requirements-dev.txt
```

Or:

```bash
pip install pytest pytest-cov pytest-xdist pytest-timeout
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests (excluding slow and network tests)
pytest -m "e2e and not slow and not network"

# Run all tests except those requiring network
pytest -m "not network"
```

### Run Specific Test Files

```bash
# Run utils tests
pytest tests/test_utils.py -v

# Run parser tests
pytest tests/test_parser.py -v

# Run all E2E tests
pytest tests/test_e2e_*.py -v
```

### Run Tests in Parallel

For faster execution:

```bash
pytest -n auto
```

### Run with Verbose Output

```bash
pytest -v --tb=short
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=polyparse --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Test Coverage

### Current Test Coverage

The test suite provides comprehensive coverage of:

1. **URL Handling** (100%)
   - Valid/invalid URL detection
   - Event slug extraction
   - URL normalization
   - Edge cases (special characters, whitespace, etc.)

2. **Price Parsing** (100%)
   - Percentage format (65%)
   - Decimal format (0.65)
   - Integer format (65 → 0.65)
   - Price extraction from text
   - Edge cases (0%, 100%, invalid input)

3. **Event Metadata Extraction** (90%)
   - Title, description, category extraction
   - Date parsing and formatting
   - Missing element handling
   - Multiple selector fallbacks

4. **Market Data Extraction** (95%)
   - Binary markets (Yes/No)
   - Multi-outcome markets
   - Price history extraction
   - Data deduplication

5. **Recurring Events** (100%)
   - Detection logic
   - Past event URL extraction
   - Multiple past events handling
   - Current event filtering

6. **CLI Functionality** (95%)
   - All command-line options
   - Error handling
   - Output formatting
   - File generation

### Coverage Goals

- Overall: ≥ 85%
- Critical paths: 100%
- Error handling: ≥ 90%

## Writing Tests

### Test Naming Convention

```python
class TestFeatureName:
    """Tests for specific feature."""

    @pytest.mark.unit
    def test_specific_behavior(self):
        """Test that specific behavior works correctly."""
        # Arrange
        input_data = "test"

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_output
```

### Using Fixtures

Common fixtures available in `conftest.py`:

```python
def test_example(mock_driver, sample_event_html, temp_output_dir):
    """Example test using fixtures."""
    # mock_driver: Mock Selenium WebDriver
    # sample_event_html: Sample HTML content
    # temp_output_dir: Temporary directory for outputs

    assert mock_driver is not None
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_with_mocks():
    """Test using mocks for external dependencies."""
    with patch('polyparse.driver.create_driver') as mock_driver:
        mock_driver.return_value = MagicMock()
        # Test code here
```

### Testing Error Conditions

```python
@pytest.mark.unit
def test_error_handling():
    """Test that errors are handled gracefully."""
    with pytest.raises(ValueError):
        function_that_should_raise_error()
```

### Data Validation Tests

```python
from tests.conftest import validate_event_data

@pytest.mark.integration
def test_data_structure():
    """Test that extracted data has valid structure."""
    data = extract_event_data(...)
    assert validate_event_data(data)
```

## CI/CD Integration

### GitHub Actions

The test suite runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### Test Matrix

Tests run on:
- **Operating Systems**: Ubuntu, macOS, Windows
- **Python Versions**: 3.8, 3.9, 3.10, 3.11

### Workflow Steps

1. **Unit Tests**: Always run (fast feedback)
2. **Integration Tests**: Run on all platforms
3. **E2E Tests (mocked)**: Run without network access
4. **E2E Tests (network)**: Run only on main branch or manual trigger
5. **Coverage Report**: Generated on Ubuntu + Python 3.11

### Running Tests Locally Like CI

```bash
# Run the same tests as CI
pytest tests/test_utils.py tests/test_parser.py -m unit -v
pytest tests/test_integration.py -m integration -v
pytest tests/test_e2e_*.py -m "e2e and not network and not slow" -v
```

## Test Data and Fixtures

### Sample Events

Test fixtures include various event types:

1. **Single Event**: Basic prediction market
   - Binary outcome (Yes/No)
   - Current prices and volume
   - Description and metadata

2. **Recurring Event**: Sports/regular events
   - Past events history
   - Multiple weeks/instances
   - Historical data

3. **Resolved Event**: Completed market
   - Final prices (1.0 / 0.0)
   - Resolution information
   - Settlement data

4. **Multi-Market Event**: Complex events
   - Multiple outcomes (> 2)
   - Various price points
   - Category-specific data

### Network Response Fixtures

Mock GraphQL and API responses for:
- Event metadata
- Market data
- Price history
- Recurring event relationships

## Troubleshooting

### Common Issues

#### 1. ChromeDriver Not Found

**Error**: `selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH`

**Solution**:
```bash
# Install ChromeDriver
pip install webdriver-manager

# Or install system-wide
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# macOS
brew install --cask chromedriver
```

#### 2. Tests Timeout

**Error**: `pytest_timeout.Timeout`

**Solution**:
- Increase timeout for slow tests
- Check network connectivity for network tests
- Use mocks for E2E tests instead of real browser

```python
@pytest.mark.timeout(60)  # 60 second timeout
def test_slow_operation():
    pass
```

#### 3. Import Errors

**Error**: `ModuleNotFoundError: No module named 'polyparse'`

**Solution**:
```bash
# Install package in development mode
pip install -e .
```

#### 4. Fixture Not Found

**Error**: `fixture 'mock_driver' not found`

**Solution**:
- Ensure `conftest.py` is in the tests directory
- Check that pytest is discovering the tests directory
- Run with `-v` flag to see which fixtures are available

#### 5. Flaky Tests

**Issue**: Tests pass sometimes but fail other times

**Solution**:
- Add explicit waits for async operations
- Use more robust selectors
- Add retry logic for network operations
- Mock external dependencies

### Debug Mode

Run tests with extra debugging:

```bash
# Show print statements
pytest -s

# Show full traceback
pytest --tb=long

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest -l
```

### Performance Profiling

Profile test execution time:

```bash
# Show slowest tests
pytest --durations=10

# Profile with cProfile
pytest --profile
```

## Best Practices

1. **Keep tests independent**: Each test should be able to run in isolation
2. **Use descriptive names**: Test names should describe what they test
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Mock external dependencies**: Don't make real network calls in unit tests
5. **Test edge cases**: Include tests for error conditions and edge cases
6. **Keep tests fast**: Unit tests should run in milliseconds
7. **Use fixtures**: Reuse test data and setup code
8. **Document complex tests**: Add comments for non-obvious test logic
9. **Maintain test data**: Keep fixtures up-to-date with API changes
10. **Run tests before committing**: Ensure all tests pass locally

## Quick Reference

```bash
# Fast feedback loop (unit tests only)
pytest -m unit -x -v

# Full local test run (excluding network)
pytest -m "not network" --cov=polyparse

# Test a specific feature
pytest tests/test_utils.py::TestURLValidation -v

# Debug a failing test
pytest tests/test_parser.py::TestPriceParsing::test_parse_percentage_format -vv --pdb

# Update test coverage report
pytest --cov=polyparse --cov-report=html && open htmlcov/index.html
```

## Contributing

When adding new features:

1. Write tests first (TDD approach recommended)
2. Ensure tests cover both happy path and error cases
3. Run full test suite before submitting PR
4. Update this documentation if adding new test categories
5. Add appropriate pytest markers
6. Include fixtures for reusable test data

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Selenium Python documentation](https://selenium-python.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
