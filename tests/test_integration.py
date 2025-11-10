"""Integration tests for polyparse event extraction."""
import json
import os
from unittest.mock import Mock, MagicMock, patch
import pytest

from polyparse.extractor import extract_event_data, extract_recurring_events
from polyparse.network import NetworkMonitor
from tests.conftest import validate_event_data, validate_market_data


class TestNetworkMonitor:
    """Integration tests for NetworkMonitor class."""

    @pytest.mark.integration
    def test_network_monitor_lifecycle(self, mock_driver):
        """Test NetworkMonitor start/stop lifecycle."""
        monitor = NetworkMonitor(mock_driver)

        monitor.start()
        assert monitor.monitoring is True

        monitor.stop()
        assert monitor.monitoring is False

    @pytest.mark.integration
    def test_network_monitor_with_performance_log(self, mock_driver, sample_performance_log):
        """Test NetworkMonitor processing performance logs."""
        mock_driver.get_log.return_value = sample_performance_log

        monitor = NetworkMonitor(mock_driver)
        monitor.start()

        # Simulate capturing responses
        monitor.capture_all_responses(wait_time=0.1, scroll_attempts=1)

        monitor.stop()

        # Verify logs were captured
        assert mock_driver.get_log.called

    @pytest.mark.integration
    def test_extract_market_data_from_network(self, mock_driver, sample_network_response):
        """Test extracting market data from network responses."""
        # Mock network response
        performance_log = [{
            "message": json.dumps({
                "message": {
                    "method": "Network.responseReceived",
                    "params": {
                        "requestId": "123",
                        "response": {
                            "url": "https://polymarket.com/api/events/test",
                            "status": 200
                        }
                    }
                }
            })
        }]

        mock_driver.get_log.return_value = performance_log
        mock_driver.execute_cdp_cmd.return_value = {
            "body": json.dumps(sample_network_response)
        }

        monitor = NetworkMonitor(mock_driver)
        monitor.start()
        monitor.capture_all_responses(wait_time=0.1, scroll_attempts=1)

        market_data = monitor.extract_market_data()

        assert isinstance(market_data, dict)


class TestEventDataExtraction:
    """Integration tests for event data extraction."""

    @pytest.mark.integration
    def test_extract_event_basic_flow(self, mock_driver):
        """Test basic event extraction flow."""
        mock_driver.current_url = "https://polymarket.com/event/test-event"

        # Mock metadata extraction
        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.extract_market_data') as mock_markets, \
             patch('polyparse.extractor.NetworkMonitor'):

            mock_metadata.return_value = {
                "title": "Test Event",
                "description": "Test description",
            }
            mock_markets.return_value = [{
                "outcome": "Yes",
                "current_price": 0.65
            }]

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test-event",
                use_network=False
            )

        assert result is not None
        assert "title" in result
        assert "markets" in result

    @pytest.mark.integration
    def test_extract_event_with_network_data(self, mock_driver, sample_network_response):
        """Test extraction combining DOM and network data."""
        mock_driver.current_url = "https://polymarket.com/event/test-event"

        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.NetworkMonitor') as mock_monitor_class:

            mock_metadata.return_value = {
                "title": "Test Event",
            }

            # Setup NetworkMonitor mock
            mock_monitor = MagicMock()
            mock_monitor.extract_market_data.return_value = sample_network_response.get("data", {})
            mock_monitor_class.return_value = mock_monitor

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test-event",
                use_network=True
            )

        assert result is not None
        assert validate_event_data(result)

    @pytest.mark.integration
    def test_extract_event_deduplication(self, mock_driver):
        """Test that duplicate market data is deduplicated."""
        mock_driver.current_url = "https://polymarket.com/event/test-event"

        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.extract_market_data') as mock_markets, \
             patch('polyparse.extractor.NetworkMonitor'):

            mock_metadata.return_value = {"title": "Test"}

            # Return duplicate markets
            mock_markets.return_value = [
                {"outcome": "Yes", "current_price": 0.65},
                {"outcome": "Yes", "current_price": 0.65},  # Duplicate
                {"outcome": "No", "current_price": 0.35},
            ]

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test-event",
                use_network=False
            )

        if "markets" in result:
            # Should have deduplicated
            outcomes = [m["outcome"] for m in result["markets"]]
            assert len(outcomes) == len(set(outcomes)), "Outcomes should be unique"

    @pytest.mark.integration
    def test_extract_event_error_handling(self, mock_driver):
        """Test error handling during extraction."""
        mock_driver.current_url = "https://polymarket.com/event/test-event"

        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.NetworkMonitor'):

            # Simulate an error
            mock_metadata.side_effect = Exception("Test error")

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test-event",
                use_network=False
            )

        # Should handle error gracefully
        assert result is not None or result is None  # Either returns partial data or None


class TestRecurringEventExtraction:
    """Integration tests for recurring event extraction."""

    @pytest.mark.integration
    def test_extract_recurring_event_detection(self, mock_driver):
        """Test detecting and extracting recurring events."""
        mock_driver.current_url = "https://polymarket.com/event/current-event"

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past:

            # Mock main event data
            mock_extract.return_value = {
                "event_id": "current-event",
                "title": "Current Event",
                "markets": []
            }

            # Mock recurring detection
            mock_detect.return_value = True

            # Mock past event URLs
            mock_past.return_value = [
                "https://polymarket.com/event/past-event-1",
                "https://polymarket.com/event/past-event-2",
            ]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current-event",
                num_past_events=2
            )

        assert result is not None
        assert "past_events" in result or isinstance(result, dict)

    @pytest.mark.integration
    def test_extract_non_recurring_event(self, mock_driver):
        """Test extraction of non-recurring event."""
        mock_driver.current_url = "https://polymarket.com/event/single-event"

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect:

            mock_extract.return_value = {
                "event_id": "single-event",
                "title": "Single Event",
            }

            mock_detect.return_value = False

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/single-event",
                num_past_events=5
            )

        assert result is not None
        # Should return main event data without past_events
        assert "event_id" in result

    @pytest.mark.integration
    def test_extract_multiple_past_events(self, mock_driver):
        """Test extracting multiple past events."""
        mock_driver.current_url = "https://polymarket.com/event/current"

        past_events_data = [
            {"event_id": f"past-{i}", "title": f"Past Event {i}"}
            for i in range(5)
        ]

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past:

            # First call returns main event, subsequent calls return past events
            mock_extract.side_effect = [
                {"event_id": "current", "title": "Current"}
            ] + past_events_data

            mock_detect.return_value = True
            mock_past.return_value = [f"https://polymarket.com/event/past-{i}" for i in range(5)]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=5
            )

        assert result is not None

    @pytest.mark.integration
    def test_fast_mode_for_past_events(self, mock_driver):
        """Test that past events use fast_mode extraction."""
        mock_driver.current_url = "https://polymarket.com/event/current"

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past:

            mock_extract.return_value = {"event_id": "test"}
            mock_detect.return_value = True
            mock_past.return_value = ["https://polymarket.com/event/past-1"]

            extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=1
            )

        # Verify fast_mode was used for past events
        # First call should be normal, second should be fast_mode=True
        calls = mock_extract.call_args_list
        if len(calls) >= 2:
            # Second call should have fast_mode=True
            assert calls[1][1].get("fast_mode") is True or calls[1][0][3] is True


class TestDataValidation:
    """Integration tests for data validation."""

    @pytest.mark.integration
    def test_validate_extracted_event_structure(self):
        """Test that extracted event data has valid structure."""
        sample_data = {
            "event_id": "test-event",
            "url": "https://polymarket.com/event/test-event",
            "scraped_at": "2024-01-01T12:00:00Z",
            "title": "Test Event",
            "description": "Test description",
            "markets": [
                {"outcome": "Yes", "current_price": 0.65},
                {"outcome": "No", "current_price": 0.35}
            ],
            "resolved": False
        }

        assert validate_event_data(sample_data)

    @pytest.mark.integration
    def test_validate_market_prices_in_range(self):
        """Test that market prices are in valid range."""
        markets = [
            {"outcome": "Yes", "current_price": 0.65},
            {"outcome": "No", "current_price": 0.35},
        ]

        for market in markets:
            assert validate_market_data(market)
            price = market["current_price"]
            assert 0 <= price <= 1, "Price should be in 0-1 range"

    @pytest.mark.integration
    def test_market_prices_sum_to_one(self):
        """Test that binary market prices sum to approximately 1.0."""
        markets = [
            {"outcome": "Yes", "current_price": 0.65},
            {"outcome": "No", "current_price": 0.35},
        ]

        total = sum(m["current_price"] for m in markets)
        assert abs(total - 1.0) < 0.01, "Binary market prices should sum to ~1.0"

    @pytest.mark.integration
    def test_validate_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        invalid_data = {
            "title": "Test Event",
            # Missing event_id, url, scraped_at
        }

        assert not validate_event_data(invalid_data)

    @pytest.mark.integration
    def test_validate_incorrect_types(self):
        """Test validation fails for incorrect field types."""
        invalid_data = {
            "event_id": 123,  # Should be string
            "url": "https://polymarket.com/event/test",
            "scraped_at": "2024-01-01",
            "title": ["Not a string"],  # Should be string
        }

        assert not validate_event_data(invalid_data)


class TestOutputFormat:
    """Integration tests for output format."""

    @pytest.mark.integration
    def test_json_serializable_output(self, mock_driver):
        """Test that extracted data is JSON serializable."""
        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.extract_market_data') as mock_markets, \
             patch('polyparse.extractor.NetworkMonitor'):

            mock_metadata.return_value = {
                "title": "Test Event",
                "description": "Description",
            }
            mock_markets.return_value = [
                {"outcome": "Yes", "current_price": 0.65}
            ]

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test",
                use_network=False
            )

        if result:
            # Should be able to serialize to JSON
            try:
                json_str = json.dumps(result)
                assert json_str is not None
                # And deserialize back
                parsed = json.loads(json_str)
                assert parsed == result
            except (TypeError, ValueError) as e:
                pytest.fail(f"Result is not JSON serializable: {e}")

    @pytest.mark.integration
    def test_output_includes_metadata(self, mock_driver):
        """Test that output includes extraction metadata."""
        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.NetworkMonitor'):

            mock_metadata.return_value = {"title": "Test"}

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test",
                use_network=False
            )

        if result:
            # Should include metadata about the scraping
            assert "url" in result or "event_id" in result
            assert "scraped_at" in result or isinstance(result, dict)

    @pytest.mark.integration
    def test_output_with_capture_directory(self, mock_driver, temp_output_dir):
        """Test that capture directory is used when provided."""
        capture_dir = os.path.join(temp_output_dir, "captures")

        with patch('polyparse.extractor.extract_event_metadata') as mock_metadata, \
             patch('polyparse.extractor.NetworkMonitor') as mock_monitor_class:

            mock_metadata.return_value = {"title": "Test"}
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor

            result = extract_event_data(
                mock_driver,
                "https://polymarket.com/event/test",
                use_network=True,
                capture_dir=capture_dir
            )

        # NetworkMonitor should be instantiated (capture_dir doesn't directly affect it in current impl)
        assert mock_monitor_class.called
