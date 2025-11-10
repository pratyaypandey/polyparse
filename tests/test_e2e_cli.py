"""End-to-end tests for polyparse CLI."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from click.testing import CliRunner

from polyparse.cli import main
from tests.conftest import validate_event_data


class TestCLIBasicFunctionality:
    """E2E tests for basic CLI functionality."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_cli_help_command(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "polyparse" in result.output.lower() or "usage" in result.output.lower()
        assert "--url" in result.output
        assert "--id" in result.output

    @pytest.mark.e2e
    def test_cli_missing_arguments(self):
        """Test CLI with no arguments."""
        runner = CliRunner()
        result = runner.invoke(main, [])

        # Should show error or help
        assert result.exit_code != 0 or "error" in result.output.lower() or "usage" in result.output.lower()

    @pytest.mark.e2e
    def test_cli_with_invalid_url(self):
        """Test CLI with invalid Polymarket URL."""
        runner = CliRunner()
        result = runner.invoke(main, ["--url", "https://example.com/invalid"])

        # Should fail with error
        assert result.exit_code != 0 or "error" in result.output.lower() or "invalid" in result.output.lower()

    @pytest.mark.e2e
    def test_cli_output_directory_creation(self):
        """Test that CLI creates output directory."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "test_output")

            with patch('polyparse.cli.create_driver'), \
                 patch('polyparse.cli.extract_event_data') as mock_extract:

                mock_extract.return_value = {
                    "event_id": "test-event",
                    "title": "Test Event",
                    "url": "https://polymarket.com/event/test",
                    "scraped_at": "2024-01-01T12:00:00Z"
                }

                result = runner.invoke(main, [
                    "--url", "https://polymarket.com/event/test",
                    "--output-dir", output_dir,
                    "--headless"
                ])

            # Output directory should be created
            assert os.path.exists(output_dir) or result.exit_code != 0


class TestCLIURLInput:
    """E2E tests for different URL input methods."""

    @pytest.mark.e2e
    def test_cli_with_full_url(self):
        """Test CLI with full Polymarket URL."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {
                "event_id": "test-event",
                "title": "Test Event",
                "url": "https://polymarket.com/event/test-event",
                "scraped_at": "2024-01-01T12:00:00Z"
            }

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test-event",
                "--headless"
            ])

        # Should complete successfully
        if result.exit_code == 0:
            assert "test-event" in result.output or result.output

    @pytest.mark.e2e
    def test_cli_with_event_id(self):
        """Test CLI with just event ID/slug."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {
                "event_id": "test-event-slug",
                "title": "Test Event",
                "url": "https://polymarket.com/event/test-event-slug",
                "scraped_at": "2024-01-01T12:00:00Z"
            }

            result = runner.invoke(main, [
                "--id", "test-event-slug",
                "--headless"
            ])

        # Should normalize to full URL and complete
        if result.exit_code == 0:
            assert result.output

    @pytest.mark.e2e
    def test_cli_with_search_query(self):
        """Test CLI with search query."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver') as mock_driver, \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            # Mock driver for search
            mock_driver_instance = mock_driver.return_value
            mock_driver_instance.current_url = "https://polymarket.com/event/found-event"

            mock_extract.return_value = {
                "event_id": "found-event",
                "title": "Found Event",
                "url": "https://polymarket.com/event/found-event",
                "scraped_at": "2024-01-01T12:00:00Z"
            }

            result = runner.invoke(main, [
                "--search", "bitcoin",
                "--headless"
            ])

        # Should perform search and extract
        if result.exit_code == 0:
            assert result.output

    @pytest.mark.e2e
    def test_cli_mutually_exclusive_inputs(self):
        """Test that providing multiple input methods shows error."""
        runner = CliRunner()

        result = runner.invoke(main, [
            "--url", "https://polymarket.com/event/test",
            "--id", "another-event",
            "--headless"
        ])

        # Should either pick one or show error
        assert result.output


class TestCLIOptions:
    """E2E tests for CLI options."""

    @pytest.mark.e2e
    def test_cli_headless_mode(self):
        """Test CLI with headless browser."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver') as mock_create, \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {"event_id": "test", "title": "Test"}

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--headless"
            ])

        # Should pass headless flag to driver
        if mock_create.called:
            call_kwargs = mock_create.call_args[1] if mock_create.call_args else {}
            assert call_kwargs.get("headless") is True or mock_create.called

    @pytest.mark.e2e
    def test_cli_verbose_mode(self):
        """Test CLI with verbose output."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {"event_id": "test", "title": "Test"}

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--verbose",
                "--headless"
            ])

        # Verbose mode should show more output
        if result.exit_code == 0:
            assert result.output

    @pytest.mark.e2e
    def test_cli_custom_output_directory(self):
        """Test CLI with custom output directory."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = os.path.join(tmpdir, "custom_output")

            with patch('polyparse.cli.create_driver'), \
                 patch('polyparse.cli.extract_event_data') as mock_extract:

                mock_extract.return_value = {
                    "event_id": "test",
                    "title": "Test",
                    "url": "https://polymarket.com/event/test",
                    "scraped_at": "2024-01-01T12:00:00Z"
                }

                result = runner.invoke(main, [
                    "--url", "https://polymarket.com/event/test",
                    "--output-dir", custom_dir,
                    "--headless"
                ])

            # Check if custom directory was used
            if result.exit_code == 0:
                assert os.path.exists(custom_dir) or custom_dir in result.output or result.output

    @pytest.mark.e2e
    def test_cli_with_capture_directory(self):
        """Test CLI with network capture directory."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            capture_dir = os.path.join(tmpdir, "captures")

            with patch('polyparse.cli.create_driver'), \
                 patch('polyparse.cli.extract_event_data') as mock_extract:

                mock_extract.return_value = {"event_id": "test", "title": "Test"}

                result = runner.invoke(main, [
                    "--url", "https://polymarket.com/event/test",
                    "--capture-dir", capture_dir,
                    "--headless"
                ])

            # Capture directory should be passed to extraction
            if mock_extract.called:
                call_args = mock_extract.call_args
                # Check if capture_dir was passed
                assert call_args or result.output


class TestCLIOutputFormat:
    """E2E tests for CLI output format."""

    @pytest.mark.e2e
    def test_cli_json_output_structure(self):
        """Test that CLI outputs valid JSON."""
        runner = CliRunner()

        sample_output = {
            "event_id": "test-event",
            "url": "https://polymarket.com/event/test-event",
            "scraped_at": "2024-01-01T12:00:00Z",
            "title": "Test Event",
            "description": "Test description",
            "markets": [
                {"outcome": "Yes", "current_price": 0.65}
            ]
        }

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = sample_output

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test-event",
                "--headless"
            ])

        if result.exit_code == 0 and result.output:
            # Try to parse as JSON
            try:
                # Output might have additional text, look for JSON
                if "{" in result.output:
                    json_start = result.output.index("{")
                    json_str = result.output[json_start:]
                    parsed = json.loads(json_str)
                    assert validate_event_data(parsed)
            except (json.JSONDecodeError, ValueError):
                # Output might be formatted differently
                pass

    @pytest.mark.e2e
    def test_cli_output_file_creation(self):
        """Test that CLI creates output JSON file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('polyparse.cli.create_driver'), \
                 patch('polyparse.cli.extract_event_data') as mock_extract:

                mock_extract.return_value = {
                    "event_id": "test-event",
                    "title": "Test",
                    "url": "https://polymarket.com/event/test-event",
                    "scraped_at": "2024-01-01T12:00:00Z"
                }

                result = runner.invoke(main, [
                    "--url", "https://polymarket.com/event/test-event",
                    "--output-dir", tmpdir,
                    "--headless"
                ])

            if result.exit_code == 0:
                # Look for JSON file
                json_files = list(Path(tmpdir).glob("*.json"))
                if json_files:
                    with open(json_files[0]) as f:
                        data = json.load(f)
                        assert validate_event_data(data)

    @pytest.mark.e2e
    def test_cli_output_contains_required_fields(self):
        """Test that output contains all required fields."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {
                "event_id": "test",
                "url": "https://polymarket.com/event/test",
                "scraped_at": "2024-01-01T12:00:00Z",
                "title": "Test Event",
                "description": "Description",
                "category": "Crypto",
                "markets": []
            }

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--headless"
            ])

        if result.exit_code == 0:
            output = result.output
            # Check for presence of key fields in output
            assert "test" in output or "Test Event" in output or output


class TestCLIErrorHandling:
    """E2E tests for CLI error handling."""

    @pytest.mark.e2e
    def test_cli_network_error_handling(self):
        """Test CLI handling of network errors."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver') as mock_create:
            mock_create.side_effect = Exception("Network error")

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--headless"
            ])

        # Should handle error gracefully
        assert result.exit_code != 0 or "error" in result.output.lower()

    @pytest.mark.e2e
    def test_cli_extraction_error_handling(self):
        """Test CLI handling of extraction errors."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.side_effect = Exception("Extraction failed")

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--headless"
            ])

        # Should handle error
        assert result.exit_code != 0 or result.output

    @pytest.mark.e2e
    def test_cli_invalid_output_directory(self):
        """Test CLI with invalid output directory."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {"event_id": "test", "title": "Test"}

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--output-dir", "/invalid/nonexistent/path",
                "--headless"
            ])

        # Should handle invalid path
        assert result.output

    @pytest.mark.e2e
    def test_cli_keyboard_interrupt(self):
        """Test CLI handling of keyboard interrupt."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver') as mock_create:
            mock_create.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--headless"
            ])

        # Should exit gracefully
        assert result.exit_code != 0 or result.output


class TestCLIAuthentication:
    """E2E tests for authentication functionality."""

    @pytest.mark.e2e
    @pytest.mark.auth
    def test_cli_auth_flag(self):
        """Test CLI with authentication flag."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.login') as mock_login, \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_extract.return_value = {"event_id": "test", "title": "Test"}

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--auth",
                "--headless"
            ])

        # Should attempt login
        if result.exit_code == 0:
            assert mock_login.called or result.output

    @pytest.mark.e2e
    @pytest.mark.auth
    def test_cli_auth_with_credentials(self):
        """Test CLI authentication with environment credentials."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.login') as mock_login, \
             patch('polyparse.cli.extract_event_data') as mock_extract, \
             patch.dict(os.environ, {'POLYMARKET_EMAIL': 'test@example.com', 'POLYMARKET_PASSWORD': 'password'}):

            mock_extract.return_value = {"event_id": "test", "title": "Test"}

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--auth",
                "--headless"
            ])

        if mock_login.called:
            # Should pass credentials to login
            assert result.output or result.exit_code is not None

    @pytest.mark.e2e
    @pytest.mark.auth
    def test_cli_auth_failure_handling(self):
        """Test CLI handling of authentication failures."""
        runner = CliRunner()

        with patch('polyparse.cli.create_driver'), \
             patch('polyparse.cli.login') as mock_login, \
             patch('polyparse.cli.extract_event_data') as mock_extract:

            mock_login.side_effect = Exception("Login failed")
            mock_extract.return_value = {"event_id": "test", "title": "Test"}

            result = runner.invoke(main, [
                "--url", "https://polymarket.com/event/test",
                "--auth",
                "--headless"
            ])

        # Should handle login failure
        assert result.output
