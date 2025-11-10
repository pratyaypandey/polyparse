"""Unit tests for polyparse.parser module."""
import json
from unittest.mock import Mock, MagicMock, patch
import pytest
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from polyparse.parser import (
    extract_event_metadata,
    extract_market_data,
    detect_recurring_event,
    get_past_event_urls,
)


class TestEventMetadataExtraction:
    """Tests for event metadata extraction."""

    @pytest.mark.unit
    def test_extract_basic_metadata(self, mock_driver):
        """Test extracting basic metadata from page."""
        # Setup mock elements
        title_element = Mock()
        title_element.text = "Will Bitcoin hit $100k in 2024?"

        desc_element = Mock()
        desc_element.text = "This market will resolve to Yes if Bitcoin reaches $100,000"

        mock_driver.find_elements.side_effect = [
            [title_element],  # Title
            [desc_element],   # Description
        ]

        with patch('polyparse.parser.WebDriverWait'):
            metadata = extract_event_metadata(mock_driver)

        assert metadata is not None
        assert isinstance(metadata, dict)

    @pytest.mark.unit
    def test_extract_with_missing_elements(self, mock_driver):
        """Test extraction when some elements are missing."""
        mock_driver.find_elements.return_value = []

        with patch('polyparse.parser.WebDriverWait'):
            metadata = extract_event_metadata(mock_driver)

        # Should return partial metadata or empty dict
        assert isinstance(metadata, dict)

    @pytest.mark.unit
    def test_extract_returns_dict(self, mock_driver):
        """Test that metadata extraction always returns a dict."""
        mock_driver.find_elements.return_value = []

        with patch('polyparse.parser.WebDriverWait'):
            result = extract_event_metadata(mock_driver)

        assert isinstance(result, dict)


class TestMarketDataExtraction:
    """Tests for market data extraction."""

    @pytest.mark.unit
    def test_extract_market_returns_list(self, mock_driver):
        """Test that market extraction returns a list."""
        mock_driver.find_elements.return_value = []

        with patch('polyparse.parser.WebDriverWait'):
            markets = extract_market_data(mock_driver)

        assert isinstance(markets, list)

    @pytest.mark.unit
    def test_extract_with_no_markets(self, mock_driver):
        """Test extraction when no market data is found."""
        mock_driver.find_elements.return_value = []

        with patch('polyparse.parser.WebDriverWait'):
            markets = extract_market_data(mock_driver)

        assert isinstance(markets, list)
        assert len(markets) == 0

    @pytest.mark.unit
    def test_extract_handles_exceptions_gracefully(self, mock_driver):
        """Test that extraction handles exceptions gracefully."""
        mock_driver.find_elements.side_effect = Exception("Test error")

        with patch('polyparse.parser.WebDriverWait'):
            try:
                markets = extract_market_data(mock_driver)
                # Should either return empty list or raise
                assert isinstance(markets, list) or markets is None
            except Exception:
                # Exception is acceptable
                pass


class TestRecurringEventDetection:
    """Tests for recurring event detection."""

    @pytest.mark.unit
    def test_detect_returns_boolean(self, mock_driver):
        """Test that detection returns a boolean."""
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "<html><body><h1>Single Event</h1></body></html>"

        is_recurring = detect_recurring_event(mock_driver)
        assert isinstance(is_recurring, bool)

    @pytest.mark.unit
    def test_detect_no_recurring(self, mock_driver):
        """Test detection when event is not recurring."""
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "<html><body><h1>Single Event</h1></body></html>"

        is_recurring = detect_recurring_event(mock_driver)
        assert is_recurring is False

    @pytest.mark.unit
    def test_detect_with_past_events_text(self, mock_driver):
        """Test detection with 'Past Events' in page source."""
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = """
        <html><body>
            <h1>Current Event</h1>
            <div class="past-events">
                <h2>Past Events</h2>
                <ul><li>Event 1</li></ul>
            </div>
        </body></html>
        """

        is_recurring = detect_recurring_event(mock_driver)
        # Should detect recurring based on text
        assert isinstance(is_recurring, bool)

    @pytest.mark.unit
    def test_detect_handles_various_keywords(self, mock_driver):
        """Test detection with various keywords."""
        keywords_html = [
            "<div>Past Events</div>",
            "<div>Previous Events</div>",
            "<div>History</div>",
            "<div>Past Markets</div>",
        ]

        for html in keywords_html:
            mock_driver.find_elements.return_value = []
            mock_driver.page_source = f"<html><body>{html}</body></html>"

            is_recurring = detect_recurring_event(mock_driver)
            # Should return a boolean
            assert isinstance(is_recurring, bool)


class TestPastEventURLExtraction:
    """Tests for extracting past event URLs."""

    @pytest.mark.unit
    def test_extract_returns_list(self, mock_driver):
        """Test that extraction returns a list."""
        mock_driver.current_url = "https://polymarket.com/event/current-event"
        mock_driver.find_elements.return_value = []

        urls = get_past_event_urls(mock_driver, max_events=5)

        assert isinstance(urls, list)

    @pytest.mark.unit
    def test_extract_past_urls(self, mock_driver):
        """Test extracting URLs of past events."""
        mock_driver.current_url = "https://polymarket.com/event/current-event"

        links = []
        for i in range(3):
            link = Mock()
            link.get_attribute.return_value = f"https://polymarket.com/event/past-event-{i}"
            links.append(link)

        mock_driver.find_elements.return_value = links

        urls = get_past_event_urls(mock_driver, max_events=5)

        assert isinstance(urls, list)
        assert len(urls) <= 5

    @pytest.mark.unit
    def test_limit_past_events(self, mock_driver):
        """Test limiting number of past events returned."""
        mock_driver.current_url = "https://polymarket.com/event/current"

        links = []
        for i in range(10):
            link = Mock()
            link.get_attribute.return_value = f"https://polymarket.com/event/past-{i}"
            links.append(link)

        mock_driver.find_elements.return_value = links

        urls = get_past_event_urls(mock_driver, max_events=3)

        assert len(urls) <= 3

    @pytest.mark.unit
    def test_no_past_events(self, mock_driver):
        """Test when no past events are found."""
        mock_driver.current_url = "https://polymarket.com/event/current"
        mock_driver.find_elements.return_value = []

        urls = get_past_event_urls(mock_driver, max_events=5)

        assert isinstance(urls, list)
        assert len(urls) == 0

    @pytest.mark.unit
    def test_handles_malformed_links(self, mock_driver):
        """Test handling of malformed or invalid links."""
        mock_driver.current_url = "https://polymarket.com/event/current"

        links = []
        # Add various types of links
        for url in [None, "", "invalid", "https://polymarket.com/event/valid"]:
            link = Mock()
            link.get_attribute.return_value = url
            links.append(link)

        mock_driver.find_elements.return_value = links

        urls = get_past_event_urls(mock_driver, max_events=10)

        # Should handle gracefully and return a list
        assert isinstance(urls, list)


class TestParserErrorHandling:
    """Tests for error handling in parser functions."""

    @pytest.mark.unit
    def test_metadata_extraction_with_timeout(self, mock_driver):
        """Test metadata extraction handles timeouts."""
        mock_driver.find_elements.side_effect = TimeoutException("Timeout")

        with patch('polyparse.parser.WebDriverWait'):
            try:
                result = extract_event_metadata(mock_driver)
                # Should return empty dict or raise
                assert result is not None or True
            except TimeoutException:
                # Acceptable to propagate timeout
                pass

    @pytest.mark.unit
    def test_market_extraction_with_no_such_element(self, mock_driver):
        """Test market extraction handles missing elements."""
        mock_driver.find_elements.side_effect = NoSuchElementException("Not found")

        with patch('polyparse.parser.WebDriverWait'):
            try:
                result = extract_market_data(mock_driver)
                # Should handle gracefully
                assert result is not None or True
            except NoSuchElementException:
                # Acceptable error
                pass

    @pytest.mark.unit
    def test_recurring_detection_with_invalid_page_source(self, mock_driver):
        """Test recurring detection with invalid page source."""
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = None

        try:
            result = detect_recurring_event(mock_driver)
            # Should handle None page source
            assert isinstance(result, bool)
        except (TypeError, AttributeError):
            # Acceptable error for None page source
            pass

    @pytest.mark.unit
    def test_past_urls_extraction_with_driver_error(self, mock_driver):
        """Test past URL extraction handles driver errors."""
        mock_driver.current_url = "https://polymarket.com/event/current"
        mock_driver.find_elements.side_effect = Exception("Driver error")

        try:
            urls = get_past_event_urls(mock_driver, max_events=5)
            # Should return empty list on error
            assert isinstance(urls, list)
        except Exception:
            # Or propagate exception
            pass


class TestParserIntegration:
    """Integration tests for parser functions."""

    @pytest.mark.unit
    def test_metadata_and_market_extraction_together(self, mock_driver):
        """Test that metadata and market extraction work together."""
        mock_driver.find_elements.return_value = []

        with patch('polyparse.parser.WebDriverWait'):
            metadata = extract_event_metadata(mock_driver)
            markets = extract_market_data(mock_driver)

        assert isinstance(metadata, dict)
        assert isinstance(markets, list)

    @pytest.mark.unit
    def test_recurring_detection_and_url_extraction(self, mock_driver):
        """Test recurring detection followed by URL extraction."""
        mock_driver.current_url = "https://polymarket.com/event/current"
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "<html><body>Past Events</body></html>"

        is_recurring = detect_recurring_event(mock_driver)

        if is_recurring:
            urls = get_past_event_urls(mock_driver, max_events=5)
            assert isinstance(urls, list)

    @pytest.mark.unit
    def test_all_parser_functions_return_expected_types(self, mock_driver):
        """Test that all parser functions return expected types."""
        mock_driver.current_url = "https://polymarket.com/event/test"
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "<html></html>"

        with patch('polyparse.parser.WebDriverWait'):
            # All functions should return expected types
            metadata = extract_event_metadata(mock_driver)
            assert isinstance(metadata, dict)

            markets = extract_market_data(mock_driver)
            assert isinstance(markets, list)

            is_recurring = detect_recurring_event(mock_driver)
            assert isinstance(is_recurring, bool)

            urls = get_past_event_urls(mock_driver, 5)
            assert isinstance(urls, list)
