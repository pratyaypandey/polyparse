"""Pytest configuration and shared fixtures for polyparse tests."""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_event_url():
    """Sample Polymarket event URL for testing."""
    return "https://polymarket.com/event/will-bitcoin-hit-100k-in-2024"


@pytest.fixture
def sample_recurring_event_url():
    """Sample recurring event URL."""
    return "https://polymarket.com/event/nfl-week-10-chiefs-vs-broncos"


@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver."""
    driver = MagicMock(spec=webdriver.Chrome)
    driver.current_url = "https://polymarket.com/event/test-event"
    driver.page_source = "<html><body></body></html>"
    driver.execute_script = MagicMock(return_value=None)
    driver.execute_cdp_cmd = MagicMock(return_value={})
    driver.find_elements = MagicMock(return_value=[])
    driver.get_log = MagicMock(return_value=[])
    return driver


@pytest.fixture
def headless_driver():
    """Create a real headless Chrome driver for E2E tests."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    yield driver

    driver.quit()


@pytest.fixture
def sample_event_html():
    """Sample HTML structure of a Polymarket event page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Will Bitcoin hit $100k in 2024? | Polymarket</title>
        <meta name="description" content="Bet on whether Bitcoin will reach $100,000 in 2024">
    </head>
    <body>
        <div id="__NEXT_DATA__" type="application/json">
        {
            "props": {
                "pageProps": {
                    "dehydratedState": {
                        "queries": [{
                            "state": {
                                "data": {
                                    "event": {
                                        "id": "will-bitcoin-hit-100k-in-2024",
                                        "title": "Will Bitcoin hit $100k in 2024?",
                                        "description": "This market will resolve to Yes if Bitcoin reaches $100,000 or more...",
                                        "category": "Crypto",
                                        "endDate": "2024-12-31T23:59:59.000Z",
                                        "resolved": false
                                    },
                                    "markets": [{
                                        "outcomes": ["Yes", "No"],
                                        "outcomePrices": [0.65, 0.35],
                                        "volume": 1500000,
                                        "liquidity": 250000
                                    }]
                                }
                            }
                        }]
                    }
                }
            }
        }
        </div>
        <h1>Will Bitcoin hit $100k in 2024?</h1>
        <div class="event-description">
            This market will resolve to Yes if Bitcoin reaches $100,000 or more by the end of 2024.
        </div>
        <div class="end-date">
            <time datetime="2024-12-31T23:59:59.000Z">Dec 31, 2024</time>
        </div>
        <div class="market-outcomes">
            <button class="outcome-yes" data-price="65">Yes 65%</button>
            <button class="outcome-no" data-price="35">No 35%</button>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_recurring_event_html():
    """Sample HTML for a recurring event with past events section."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NFL Week 10: Chiefs vs Broncos | Polymarket</title>
    </head>
    <body>
        <h1>NFL Week 10: Chiefs vs Broncos</h1>
        <div class="event-description">
            Will the Kansas City Chiefs beat the Denver Broncos in Week 10?
        </div>
        <div class="market-outcomes">
            <button class="outcome-yes" data-price="72">Chiefs Win 72%</button>
            <button class="outcome-no" data-price="28">Broncos Win 28%</button>
        </div>
        <div class="past-events">
            <h2>Past Events</h2>
            <ul>
                <li><a href="/event/nfl-week-9-chiefs-vs-dolphins">Week 9: Chiefs vs Dolphins</a></li>
                <li><a href="/event/nfl-week-8-chiefs-vs-raiders">Week 8: Chiefs vs Raiders</a></li>
                <li><a href="/event/nfl-week-7-chiefs-vs-49ers">Week 7: Chiefs vs 49ers</a></li>
            </ul>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_network_response():
    """Sample network response with market data."""
    return {
        "data": {
            "event": {
                "id": "will-bitcoin-hit-100k-in-2024",
                "title": "Will Bitcoin hit $100k in 2024?",
                "description": "This market will resolve to Yes if Bitcoin reaches $100,000 or more by the end of 2024.",
                "category": "Crypto",
                "endDate": "2024-12-31T23:59:59.000Z",
                "resolved": False,
                "markets": [
                    {
                        "outcomes": ["Yes", "No"],
                        "outcomePrices": [0.65, 0.35],
                        "volume": 1500000,
                        "liquidity": 250000,
                        "priceHistory": [
                            {"timestamp": "2024-01-01T00:00:00Z", "price": 0.45},
                            {"timestamp": "2024-03-01T00:00:00Z", "price": 0.55},
                            {"timestamp": "2024-06-01T00:00:00Z", "price": 0.62},
                            {"timestamp": "2024-09-01T00:00:00Z", "price": 0.65}
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_performance_log():
    """Sample Chrome performance log entries."""
    return [
        {
            "message": json.dumps({
                "message": {
                    "method": "Network.requestWillBeSent",
                    "params": {
                        "requestId": "1234",
                        "request": {
                            "url": "https://polymarket.com/api/events/will-bitcoin-hit-100k-in-2024"
                        }
                    }
                }
            })
        },
        {
            "message": json.dumps({
                "message": {
                    "method": "Network.responseReceived",
                    "params": {
                        "requestId": "1234",
                        "response": {
                            "url": "https://polymarket.com/api/events/will-bitcoin-hit-100k-in-2024",
                            "status": 200,
                            "mimeType": "application/json"
                        }
                    }
                }
            })
        },
        {
            "message": json.dumps({
                "message": {
                    "method": "Network.loadingFinished",
                    "params": {
                        "requestId": "1234"
                    }
                }
            })
        }
    ]


@pytest.fixture
def expected_event_structure():
    """Expected structure of extracted event data."""
    return {
        "event_id": str,
        "url": str,
        "scraped_at": str,
        "title": str,
        "description": str,
        "category": str,
        "end_date": str,
        "resolved": bool,
        "markets": list,
    }


@pytest.fixture
def expected_market_structure():
    """Expected structure of market data."""
    return {
        "outcome": str,
        "current_price": float,
    }


def validate_event_data(data: Dict[str, Any]) -> bool:
    """Validate that event data has the expected structure and types."""
    required_fields = ["event_id", "url", "scraped_at", "title"]

    # Check required fields exist
    for field in required_fields:
        if field not in data:
            return False

    # Check types
    if not isinstance(data.get("event_id"), str):
        return False
    if not isinstance(data.get("url"), str):
        return False
    if not isinstance(data.get("title"), str):
        return False
    if "markets" in data and not isinstance(data["markets"], list):
        return False
    if "resolved" in data and not isinstance(data["resolved"], bool):
        return False

    return True


def validate_market_data(market: Dict[str, Any]) -> bool:
    """Validate that market data has expected structure."""
    if not isinstance(market.get("outcome"), str):
        return False
    if "current_price" in market:
        price = market["current_price"]
        if not isinstance(price, (int, float)):
            return False
        if not (0 <= price <= 1):
            return False
    return True


# Export validation functions for use in tests
__all__ = [
    "validate_event_data",
    "validate_market_data",
]
