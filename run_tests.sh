#!/bin/bash
# Test runner script for Polyparse
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_E2E=true
RUN_NETWORK=false
COVERAGE=false
VERBOSE=false
PARALLEL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            RUN_E2E=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            RUN_E2E=false
            shift
            ;;
        --e2e-only)
            RUN_UNIT=false
            RUN_INTEGRATION=false
            shift
            ;;
        --with-network)
            RUN_NETWORK=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --unit-only        Run only unit tests"
            echo "  --integration-only Run only integration tests"
            echo "  --e2e-only        Run only E2E tests"
            echo "  --with-network    Include network tests (slower)"
            echo "  --coverage        Generate coverage report"
            echo "  -v, --verbose     Verbose output"
            echo "  -p, --parallel    Run tests in parallel"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh --unit-only -v"
            echo "  ./run_tests.sh --coverage"
            echo "  ./run_tests.sh --e2e-only --with-network"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== Polyparse Test Runner ===${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov pytest-xdist"
    exit 1
fi

# Build pytest command
PYTEST_CMD="pytest"
PYTEST_ARGS=""

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=polyparse --cov-report=html --cov-report=term"
fi

PYTEST_ARGS="$PYTEST_ARGS --tb=short"

# Build marker expression
MARKERS=""

if [ "$RUN_UNIT" = true ]; then
    echo -e "${YELLOW}Running unit tests...${NC}"
    $PYTEST_CMD tests/test_utils.py tests/test_parser.py -m unit $PYTEST_ARGS
    echo ""
fi

if [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}Running integration tests...${NC}"
    $PYTEST_CMD tests/test_integration.py -m integration $PYTEST_ARGS
    echo ""
fi

if [ "$RUN_E2E" = true ]; then
    echo -e "${YELLOW}Running E2E tests...${NC}"

    if [ "$RUN_NETWORK" = true ]; then
        # Run all E2E tests including network tests
        $PYTEST_CMD tests/test_e2e_cli.py tests/test_e2e_recurring.py -m e2e $PYTEST_ARGS
    else
        # Skip network and slow tests
        $PYTEST_CMD tests/test_e2e_cli.py tests/test_e2e_recurring.py -m "e2e and not network and not slow" $PYTEST_ARGS
    fi
    echo ""
fi

# Summary
echo -e "${GREEN}=== Test Run Complete ===${NC}"

if [ "$COVERAGE" = true ]; then
    echo ""
    echo -e "${GREEN}Coverage report generated:${NC}"
    echo "  HTML: htmlcov/index.html"
    echo "  Open with: open htmlcov/index.html"
fi

echo ""
echo -e "${GREEN}All tests passed!${NC}"
