"""Unit tests for polyparse.utils module."""
import pytest
from polyparse.utils import (
    is_polymarket_url,
    extract_slug_from_url,
    extract_event_id_from_url,
    normalize_to_url,
)


class TestURLValidation:
    """Tests for URL validation functions."""

    @pytest.mark.unit
    def test_valid_polymarket_urls(self):
        """Test that valid Polymarket URLs are recognized."""
        valid_urls = [
            "https://polymarket.com/event/test-event",
            "https://polymarket.com/event/test-event-123",
            "https://www.polymarket.com/event/another-event",
            "http://polymarket.com/event/http-url",  # Should work even with http
        ]
        for url in valid_urls:
            assert is_polymarket_url(url), f"Should recognize {url} as valid"

    @pytest.mark.unit
    def test_invalid_polymarket_urls(self):
        """Test that invalid URLs are rejected."""
        invalid_urls = [
            "https://example.com/event/test",
            "https://polymarket.com/invalid-path",
            "not-a-url",
            "",
        ]
        for url in invalid_urls:
            assert not is_polymarket_url(url), f"Should reject {url} as invalid"

    @pytest.mark.unit
    def test_url_with_query_params(self):
        """Test URLs with query parameters."""
        url = "https://polymarket.com/event/test-event?ref=123"
        assert is_polymarket_url(url)

    @pytest.mark.unit
    def test_url_with_trailing_slash(self):
        """Test URLs with trailing slashes."""
        url = "https://polymarket.com/event/test-event/"
        assert is_polymarket_url(url)


class TestEventSlugExtraction:
    """Tests for event slug extraction."""

    @pytest.mark.unit
    def test_extract_from_full_url(self):
        """Test extracting slug from full URL."""
        url = "https://polymarket.com/event/will-bitcoin-hit-100k"
        assert extract_slug_from_url(url) == "will-bitcoin-hit-100k"

    @pytest.mark.unit
    def test_extract_from_url_with_params(self):
        """Test extracting slug from URL with query parameters."""
        url = "https://polymarket.com/event/test-event?ref=twitter&utm=123"
        assert extract_slug_from_url(url) == "test-event"

    @pytest.mark.unit
    def test_extract_with_trailing_slash(self):
        """Test extracting from URL with trailing slash."""
        url = "https://polymarket.com/event/test-event/"
        assert extract_slug_from_url(url) == "test-event"

    @pytest.mark.unit
    def test_extract_from_www_url(self):
        """Test extracting from URL with www subdomain."""
        url = "https://www.polymarket.com/event/my-event"
        assert extract_slug_from_url(url) == "my-event"

    @pytest.mark.unit
    def test_invalid_url_returns_none(self):
        """Test that invalid inputs return None."""
        invalid_inputs = [
            "not/a/valid/path",
            "",
        ]
        for inp in invalid_inputs:
            result = extract_slug_from_url(inp)
            assert result is None

    @pytest.mark.unit
    def test_extract_from_non_polymarket_url(self):
        """Test extracting from non-Polymarket URL still extracts pattern."""
        url = "https://example.com/event/test"
        # The regex will match /event/ pattern regardless of domain
        result = extract_slug_from_url(url)
        assert result == "test"  # Regex matches the pattern

    @pytest.mark.unit
    def test_extract_event_id_same_as_slug(self):
        """Test that event ID extraction works the same as slug."""
        url = "https://polymarket.com/event/test-event-id"
        assert extract_event_id_from_url(url) == "test-event-id"
        assert extract_slug_from_url(url) == "test-event-id"


class TestURLNormalization:
    """Tests for URL normalization."""

    @pytest.mark.unit
    def test_normalize_full_url(self):
        """Test that full URLs are validated."""
        url = "https://polymarket.com/event/test-event"
        assert normalize_to_url(url, "url") == url

    @pytest.mark.unit
    def test_normalize_url_without_protocol(self):
        """Test URL without protocol gets https added."""
        url = "polymarket.com/event/test-event"
        result = normalize_to_url(url, "url")
        assert result.startswith("https://")
        assert "polymarket.com" in result

    @pytest.mark.unit
    def test_normalize_id_to_url(self):
        """Test converting event ID to full URL."""
        event_id = "test-event"
        expected = "https://polymarket.com/event/test-event"
        assert normalize_to_url(event_id, "id") == expected

    @pytest.mark.unit
    def test_normalize_id_with_leading_slash(self):
        """Test ID with leading slash."""
        event_id = "/event/test-event"
        result = normalize_to_url(event_id, "id")
        assert "polymarket.com/event/test-event" in result

    @pytest.mark.unit
    def test_normalize_search_query(self):
        """Test search query normalization."""
        query = "bitcoin"
        result = normalize_to_url(query, "search")
        assert "polymarket.com/search?q=bitcoin" in result

    @pytest.mark.unit
    def test_normalize_invalid_type_raises(self):
        """Test that invalid input type raises error."""
        with pytest.raises(ValueError):
            normalize_to_url("test", "invalid_type")

    @pytest.mark.unit
    def test_normalize_non_polymarket_url_raises(self):
        """Test that non-Polymarket URL raises error."""
        with pytest.raises(ValueError):
            normalize_to_url("https://example.com/event/test", "url")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit
    def test_empty_string(self):
        """Test handling of empty strings."""
        assert not is_polymarket_url("")
        assert extract_slug_from_url("") is None

    @pytest.mark.unit
    def test_none_value(self):
        """Test handling of None values."""
        with pytest.raises((TypeError, AttributeError)):
            is_polymarket_url(None)

    @pytest.mark.unit
    def test_special_characters_in_id(self):
        """Test IDs with special characters."""
        event_id = "test-event-2024-50"
        result = normalize_to_url(event_id, "id")
        assert "polymarket.com/event/" in result
        assert event_id in result

    @pytest.mark.unit
    def test_very_long_id(self):
        """Test handling of very long IDs."""
        long_id = "a" * 200
        result = normalize_to_url(long_id, "id")
        assert long_id in result

    @pytest.mark.unit
    def test_id_with_uppercase(self):
        """Test IDs with uppercase letters."""
        event_id = "Test-Event-With-CAPS"
        result = normalize_to_url(event_id, "id")
        assert event_id in result  # Should preserve the case

    @pytest.mark.unit
    def test_extract_from_url_with_hash(self):
        """Test extracting slug from URL with hash fragment."""
        url = "https://polymarket.com/event/test-event#section"
        # Regex stops at ? or /, so hash will be included
        result = extract_slug_from_url(url)
        # The implementation captures until /?
        assert "test-event" in result
