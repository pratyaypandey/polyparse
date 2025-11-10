# Polyparse

A CLI tool that uses Selenium to scrape Polymarket event data, including historical prices, and save it to structured JSON files.

## Features

- Scrape comprehensive event data from Polymarket
- Extract market outcomes, prices, volumes, and liquidity
- Capture historical price data when available
- Handle recurring events with automatic past event scraping
- Support multiple input methods: URL, event ID, or search query
- Optional authentication for accessing additional data
- Save data to structured JSON files

## Installation

### Via Homebrew (macOS/Linux)

```bash
# Once published to Homebrew
brew install polyparse

# Or from a custom tap
brew tap pratyaypandey/polyparse
brew install polyparse
```

### Via pip

```bash
pip install polyparse
```

### From source

```bash
git clone https://github.com/pratyaypandey/polyparse.git
cd polyparse
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Scrape an event by URL:
```bash
polyparse --url https://polymarket.com/event/your-event-slug
```

Scrape by event ID:
```bash
polyparse --id your-event-slug
```

Search for an event:
```bash
polyparse --search "event search query"
```

### Options

- `--url`: Polymarket event URL
- `--id`: Polymarket event ID or slug
- `--search`: Search query to find event
- `--output-dir`: Output directory for JSON files (default: `./polyparse_data`)
- `--past-events`: Number of past events to scrape for recurring events (will prompt if not provided)
- `--auth`: Enable authentication (will prompt for credentials)
- `--headless`: Run browser in headless mode
- `--verbose`: Verbose output

### Examples

Scrape with past events:
```bash
polyparse --url https://polymarket.com/event/example --past-events 5
```

Scrape with authentication:
```bash
polyparse --id example-event --auth
```

Headless mode:
```bash
polyparse --url https://polymarket.com/event/example --headless
```

## Output Format

The tool saves data in JSON format with the following structure:

```json
{
  "event_id": "event-slug",
  "url": "https://polymarket.com/event/event-slug",
  "scraped_at": "2024-01-01T12:00:00Z",
  "title": "Event Title",
  "description": "Event description...",
  "category": "Category",
  "end_date": "2024-12-31",
  "resolved": false,
  "markets": [
    {
      "outcome": "Yes",
      "current_price": 0.65,
      "volume": 100000.0,
      "liquidity": 100000.0,
      "price_history": [
        {"timestamp": "2024-01-01T00:00:00Z", "price": 0.60}
      ]
    }
  ],
  "past_events": []
}
```

## Requirements

- Python 3.8+
- Chrome browser (for Selenium)
- ChromeDriver (automatically managed by webdriver-manager)

## Notes

- The tool uses Selenium to scrape data, so it requires a browser to be available
- Rate limiting: The tool includes delays to be respectful to Polymarket's servers
- Some data may require authentication to access
- Historical price data extraction depends on what's available on the page

## Development

### Running Tests

```bash
pytest
```

### Building from Source

```bash
python -m build
```

## Distribution

For information on how to distribute this package via Homebrew and PyPI, see [DISTRIBUTION.md](DISTRIBUTION.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

