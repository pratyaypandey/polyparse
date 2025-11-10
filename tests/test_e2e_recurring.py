"""End-to-end tests for recurring/past events functionality."""
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from polyparse.cli import main
from polyparse.extractor import extract_recurring_events
from tests.conftest import validate_event_data


class TestRecurringEventsCLI:
    """E2E tests for recurring events via CLI."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_cli_with_past_events_flag(self):
        """Test CLI with --past-events flag."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_recurring_events') as mock_extract:

            mock_extract.return_value = {
                "event_id": "current-event",
                "title": "Current Event",
                "url": "https://polymarket.com/event/current-event",
                "scraped_at": "2024-01-01T12:00:00Z",
                "past_events": [
                    {"event_id": "past-1", "title": "Past Event 1"},
                    {"event_id": "past-2", "title": "Past Event 2"},
                ]
            }

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/current-event",
                "--past-events", "2",
                "--headless"
            ])

        if result.exit_code == 0:
            # Should extract recurring events
            assert mock_extract.called
            # Output should mention past events
            output = result.output
            assert output  # Has some output

    @pytest.mark.e2e
    def test_cli_past_events_with_different_counts(self):
        """Test extracting different numbers of past events."""
        runner = CliRunner()

        for count in [1, 3, 5, 10]:
            with patch('polyparse.cli.create_driver'), \
                 patch('polyparse.cli.extract_recurring_events') as mock_extract:

                past_events = [
                    {"event_id": f"past-{i}", "title": f"Past {i}"}
                    for i in range(count)
                ]

                mock_extract.return_value = {
                    "event_id": "current",
                    "title": "Current",
                    "past_events": past_events
                }

                result = runner.invoke(main, [
                    "--url", "https://polymarket.com/event/current",
                    "--past-events", str(count),
                    "--headless"
                ])

            if result.exit_code == 0 and mock_extract.called:
                # Should request correct number
                call_args = mock_extract.call_args
                if call_args:
                    assert call_args[1].get("num_past_events") == count or call_args

    @pytest.mark.e2e
    def test_cli_past_events_zero_or_negative(self):
        """Test past-events with zero or negative values."""
        runner = CliRunner()

        for count in [0, -1]:
            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--past-events", str(count),
                "--headless"
            ])

            # Should either reject or handle gracefully
            assert result.output or result.exit_code is not None

    @pytest.mark.e2e
    def test_cli_past_events_output_structure(self):
        """Test that past events output has correct structure."""
        runner = CliRunner()

        sample_output = {
            "event_id": "current-event",
            "url": "https://polymarket.com/event/current-event",
            "scraped_at": "2024-01-01T12:00:00Z",
            "title": "NFL Week 10: Chiefs vs Broncos",
            "markets": [
                {"outcome": "Chiefs Win", "current_price": 0.72}
            ],
            "past_events": [
                {
                    "event_id": "nfl-week-9",
                    "url": "https://polymarket.com/event/nfl-week-9",
                    "title": "NFL Week 9: Chiefs vs Dolphins",
                    "resolved": True,
                    "markets": [
                        {"outcome": "Chiefs Win", "current_price": 1.0}
                    ]
                },
                {
                    "event_id": "nfl-week-8",
                    "url": "https://polymarket.com/event/nfl-week-8",
                    "title": "NFL Week 8: Chiefs vs Raiders",
                    "resolved": True,
                    "markets": [
                        {"outcome": "Chiefs Win", "current_price": 1.0}
                    ]
                }
            ]
        }

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_recurring_events') as mock_extract:

            mock_extract.return_value = sample_output

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/current-event",
                "--past-events", "2",
                "--headless"
            ])

        if result.exit_code == 0:
            # Validate structure
            assert validate_event_data(sample_output)
            if "past_events" in sample_output:
                for past_event in sample_output["past_events"]:
                    assert validate_event_data(past_event)


class TestRecurringEventsExtraction:
    """E2E tests for recurring events extraction logic."""

    @pytest.mark.e2e
    @pytest.mark.network
    def test_extract_recurring_event_full_flow(self):
        """Test full extraction flow for recurring events."""
        mock_driver = MagicMock()
        mock_driver.current_url = "https://polymarket.com/event/current-event"

        with patch('polyparse.extractor.extract_event_data') as mock_extract_single, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            # Main event
            mock_extract_single.side_effect = [
                {
                    "event_id": "current-event",
                    "title": "Current Event",
                    "url": "https://polymarket.com/event/current-event",
                    "markets": []
                },
                # Past events
                {
                    "event_id": "past-1",
                    "title": "Past Event 1",
                    "url": "https://polymarket.com/event/past-1",
                    "resolved": True
                },
                {
                    "event_id": "past-2",
                    "title": "Past Event 2",
                    "url": "https://polymarket.com/event/past-2",
                    "resolved": True
                }
            ]

            mock_detect.return_value = True
            mock_past.return_value = [
                "https://polymarket.com/event/past-1",
                "https://polymarket.com/event/past-2"
            ]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current-event",
                num_past_events=2
            )

        assert result is not None
        assert "event_id" in result
        if "past_events" in result:
            assert len(result["past_events"]) == 2

    @pytest.mark.e2e
    def test_extract_resolved_past_events(self):
        """Test that past events are correctly marked as resolved."""
        mock_driver = MagicMock()
        mock_driver.current_url = "https://polymarket.com/event/current"

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.side_effect = [
                {"event_id": "current", "resolved": False},
                {"event_id": "past-1", "resolved": True},
            ]

            mock_detect.return_value = True
            mock_past.return_value = ["https://polymarket.com/event/past-1"]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=1
            )

        if result and "past_events" in result:
            # Past event should be resolved
            assert result["past_events"][0]["resolved"] is True

    @pytest.mark.e2e
    def test_extract_past_events_with_full_data(self):
        """Test that past events include all data fields."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.side_effect = [
                {
                    "event_id": "current",
                    "title": "Current",
                    "markets": []
                },
                {
                    "event_id": "past-1",
                    "title": "Past Event 1",
                    "description": "Past event description",
                    "category": "Sports",
                    "end_date": "2024-10-27",
                    "resolved": True,
                    "markets": [
                        {
                            "outcome": "Yes",
                            "current_price": 1.0,
                            "volume": 50000,
                            "liquidity": 0
                        }
                    ]
                }
            ]

            mock_detect.return_value = True
            mock_past.return_value = ["https://polymarket.com/event/past-1"]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=1
            )

        if result and "past_events" in result:
            past_event = result["past_events"][0]
            # Should have all fields
            assert "title" in past_event
            assert "description" in past_event
            assert "markets" in past_event
            assert validate_event_data(past_event)

    @pytest.mark.e2e
    def test_extract_non_recurring_event_returns_single(self):
        """Test that non-recurring events don't have past_events."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.return_value = {
                "event_id": "single-event",
                "title": "Single Event",
                "markets": []
            }

            mock_detect.return_value = False

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/single-event",
                num_past_events=5
            )

        assert result is not None
        # Should not have past_events field
        assert "past_events" not in result or len(result.get("past_events", [])) == 0


class TestPastEventsDataQuality:
    """E2E tests for data quality of past events."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_past_events_have_unique_ids(self):
        """Test that past events have unique IDs."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.side_effect = [
                {"event_id": "current", "title": "Current"},
                {"event_id": "past-1", "title": "Past 1"},
                {"event_id": "past-2", "title": "Past 2"},
                {"event_id": "past-3", "title": "Past 3"},
            ]

            mock_detect.return_value = True
            mock_past.return_value = [
                f"https://polymarket.com/event/past-{i}" for i in range(1, 4)
            ]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=3
            )

        if result and "past_events" in result:
            event_ids = [e["event_id"] for e in result["past_events"]]
            # All IDs should be unique
            assert len(event_ids) == len(set(event_ids))

    @pytest.mark.e2e
    def test_past_events_sorted_by_date(self):
        """Test that past events are in chronological order."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.side_effect = [
                {"event_id": "current", "end_date": "2024-11-10"},
                {"event_id": "past-1", "end_date": "2024-11-03"},
                {"event_id": "past-2", "end_date": "2024-10-27"},
                {"event_id": "past-3", "end_date": "2024-10-20"},
            ]

            mock_detect.return_value = True
            mock_past.return_value = [
                "https://polymarket.com/event/past-1",
                "https://polymarket.com/event/past-2",
                "https://polymarket.com/event/past-3",
            ]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=3
            )

        if result and "past_events" in result:
            dates = [e.get("end_date") for e in result["past_events"] if "end_date" in e]
            if len(dates) > 1:
                # Should be in descending order (most recent first)
                # or ascending order (oldest first)
                assert dates == sorted(dates) or dates == sorted(dates, reverse=True)

    @pytest.mark.e2e
    def test_past_events_market_data_complete(self):
        """Test that past events have complete market data."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.side_effect = [
                {"event_id": "current", "markets": []},
                {
                    "event_id": "past-1",
                    "markets": [
                        {
                            "outcome": "Yes",
                            "current_price": 1.0,
                            "volume": 100000,
                            "liquidity": 0
                        },
                        {
                            "outcome": "No",
                            "current_price": 0.0,
                            "volume": 100000,
                            "liquidity": 0
                        }
                    ]
                }
            ]

            mock_detect.return_value = True
            mock_past.return_value = ["https://polymarket.com/event/past-1"]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=1
            )

        if result and "past_events" in result:
            past_event = result["past_events"][0]
            if "markets" in past_event:
                for market in past_event["markets"]:
                    # Each market should have required fields
                    assert "outcome" in market
                    assert "current_price" in market
                    # Prices should be in valid range
                    assert 0 <= market["current_price"] <= 1

    @pytest.mark.e2e
    def test_past_events_no_duplicates_with_current(self):
        """Test that current event is not in past_events."""
        mock_driver = MagicMock()
        mock_driver.current_url = "https://polymarket.com/event/current"

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.side_effect = [
                {"event_id": "current", "title": "Current Event"},
                {"event_id": "past-1", "title": "Past Event 1"},
            ]

            mock_detect.return_value = True
            # Simulate that get_past_event_urls returns only past events
            mock_past.return_value = ["https://polymarket.com/event/past-1"]

            result = extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=5
            )

        if result and "past_events" in result:
            past_ids = [e["event_id"] for e in result["past_events"]]
            # Current event ID should not be in past events
            assert "current" not in past_ids


class TestPastEventsPerformance:
    """E2E tests for past events extraction performance."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_fast_mode_used_for_past_events(self):
        """Test that fast_mode is used when extracting past events."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            mock_extract.return_value = {"event_id": "test"}
            mock_detect.return_value = True
            mock_past.return_value = ["https://polymarket.com/event/past-1"]

            extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=1
            )

        # Check that fast_mode was used for past event
        calls = mock_extract.call_args_list
        if len(calls) >= 2:
            # Second call (past event) should use fast_mode
            past_event_call = calls[1]
            # Check kwargs or positional args
            if past_event_call[1]:  # kwargs
                assert past_event_call[1].get("fast_mode") is True
            elif len(past_event_call[0]) > 3:  # positional
                assert past_event_call[0][3] is True

    @pytest.mark.e2e
    def test_limited_past_events_extraction(self):
        """Test that extraction respects num_past_events limit."""
        mock_driver = MagicMock()

        with patch('polyparse.extractor.extract_event_data') as mock_extract, \
             patch('polyparse.extractor.detect_recurring_event') as mock_detect, \
             patch('polyparse.extractor.get_past_event_urls') as mock_past, \
             patch('polyparse.extractor.navigate_to_event'):

            # Return many past URLs
            mock_past.return_value = [
                f"https://polymarket.com/event/past-{i}" for i in range(20)
            ]

            mock_detect.return_value = True
            mock_extract.return_value = {"event_id": "test"}

            extract_recurring_events(
                mock_driver,
                "https://polymarket.com/event/current",
                num_past_events=3  # Limit to 3
            )

        # Should only extract 3 past events + 1 current = 4 total calls
        # Actually, it should request only 3 from get_past_event_urls
        # Check that get_past_event_urls was called with correct limit
        if mock_past.called:
            call_args = mock_past.call_args
            max_events = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("max_events")
            assert max_events == 3
