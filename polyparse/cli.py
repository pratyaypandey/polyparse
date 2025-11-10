import click
import json
import os
import time
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from .driver import create_driver, enable_network_logging
from .auth import login
from .utils import normalize_to_url, extract_slug_from_url
from .extractor import extract_event_data, extract_recurring_events


@click.command()
@click.option("--url", help="Polymarket event URL")
@click.option("--id", help="Polymarket event ID or slug")
@click.option("--search", help="Search query to find event")
@click.option("--output-dir", default="./polyparse_data", help="Output directory for JSON files")
@click.option("--capture-dir", default=None, help="Directory to save all captured network responses")
@click.option("--past-events", type=int, help="Number of past events to scrape for recurring events")
@click.option("--auth", is_flag=True, help="Enable authentication")
@click.option("--headless", is_flag=True, help="Run browser in headless mode")
@click.option("--verbose", is_flag=True, help="Verbose output")
def main(url, id, search, output_dir, capture_dir, past_events, auth, headless, verbose):
    if not any([url, id, search]):
        click.echo("Error: Must provide --url, --id, or --search")
        return
    
    input_type = "url" if url else ("id" if id else "search")
    input_value = url or id or search
    
    try:
        event_url = normalize_to_url(input_value, input_type)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return
    
    if input_type == "search":
        click.echo(f"Searching for: {input_value}")
        click.echo("Note: Search functionality requires navigating to search results")
    
    if verbose:
        click.echo(f"Target URL: {event_url}")
    
    driver = None
    try:
        driver = create_driver(headless=headless)
        
        if auth:
            if verbose:
                click.echo("Attempting to log in...")
            login_success = login(driver)
            if login_success:
                click.echo("Login successful")
            else:
                click.echo("Login failed or skipped")
        
        if input_type == "search":
            driver.get(event_url)
            time.sleep(3)
            event_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/event/']")
            if event_links:
                event_url = event_links[0].get_attribute("href")
                if verbose:
                    click.echo(f"Found event: {event_url}")
            else:
                click.echo("Error: No event found in search results")
                return
        
        if past_events is None:
            past_events = click.prompt("How many past events to scrape?", type=int, default=0)
        
        click.echo(f"Scraping event: {event_url}")
        if past_events > 0:
            click.echo(f"Will scrape {past_events} past events")
        
        if capture_dir:
            click.echo(f"Capturing all network responses to: {capture_dir}")
            os.makedirs(capture_dir, exist_ok=True)
        
        if past_events > 0:
            click.echo("Extracting main event data...")
            event_data = extract_recurring_events(driver, event_url, past_events, capture_dir=capture_dir)
            click.echo(f"Scraped {len(event_data.get('past_events', []))} past events")
        else:
            click.echo("Extracting event data...")
            event_data = extract_event_data(driver, event_url, capture_dir=capture_dir)
        
        click.echo(f"Found {len(event_data.get('markets', []))} market outcomes")
        
        os.makedirs(output_dir, exist_ok=True)
        
        slug = extract_slug_from_url(event_url) or event_data.get("event_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{slug}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(event_data, f, indent=2, ensure_ascii=False)
        
        click.echo(f"✓ Data saved to: {filepath}")
        click.echo(f"  Event: {event_data.get('title', 'Unknown')}")
        click.echo(f"  Markets: {len(event_data.get('markets', []))}")
        if past_events > 0:
            click.echo(f"  Past events: {len(event_data.get('past_events', []))}")
        
    except WebDriverException as e:
        click.echo(f"Error: WebDriver error - {e}")
    except Exception as e:
        click.echo(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()

