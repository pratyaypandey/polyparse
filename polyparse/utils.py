import re
from urllib.parse import urlparse, urljoin


POLYMARKET_BASE_URL = "https://polymarket.com"


def normalize_to_url(input_value, input_type):
    if input_type == "url":
        if not input_value.startswith(("http://", "https://")):
            input_value = "https://" + input_value
        if "polymarket.com" not in input_value:
            raise ValueError("URL must be a Polymarket URL")
        return input_value
    
    elif input_type == "id":
        if input_value.startswith("/"):
            return urljoin(POLYMARKET_BASE_URL, input_value)
        return urljoin(POLYMARKET_BASE_URL, f"/event/{input_value}")
    
    elif input_type == "search":
        return urljoin(POLYMARKET_BASE_URL, f"/search?q={input_value}")
    
    raise ValueError(f"Unknown input type: {input_type}")


def extract_event_id_from_url(url):
    match = re.search(r'/event/([^/?]+)', url)
    if match:
        return match.group(1)
    return None


def extract_slug_from_url(url):
    match = re.search(r'/event/([^/?]+)', url)
    if match:
        return match.group(1)
    return None


def is_polymarket_url(url):
    return "polymarket.com" in url and "/event/" in url


