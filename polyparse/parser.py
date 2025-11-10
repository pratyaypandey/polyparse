from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .driver import wait_for_element, wait_for_elements, safe_get_text
import time
import re


def navigate_to_event(driver, url, fast_mode=False):
    driver.get(url)
    if fast_mode:
        time.sleep(1.5)
    else:
        time.sleep(3)
    
    WebDriverWait(driver, 10 if fast_mode else 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    if not fast_mode:
        time.sleep(2)


def extract_event_metadata(driver):
    metadata = {}
    
    title_selectors = [
        "h1",
        "[data-testid='event-title']",
        ".event-title",
        "h1[class*='title']",
        "title",
    ]
    
    for selector in title_selectors:
        title = safe_get_text(driver, By.CSS_SELECTOR, selector, timeout=2)
        if title and len(title) > 0 and len(title) < 500:
            metadata["title"] = title
            break
    
    if "title" not in metadata:
        page_title = driver.title
        if page_title:
            metadata["title"] = page_title.split("|")[0].strip()
    
    description_selectors = [
        "[data-testid='event-description']",
        ".event-description",
        "[class*='description']",
        "meta[name='description']",
    ]
    
    for selector in description_selectors:
        if selector.startswith("meta"):
            desc_elem = wait_for_element(driver, By.CSS_SELECTOR, selector, timeout=2)
            if desc_elem:
                desc = desc_elem.get_attribute("content")
            else:
                desc = ""
        else:
            desc = safe_get_text(driver, By.CSS_SELECTOR, selector, timeout=2)
        
        if desc and len(desc) > 20:
            metadata["description"] = desc
            break
    
    category_elem = wait_for_element(driver, By.CSS_SELECTOR, "[class*='category'], [data-testid='category'], [class*='tag']", timeout=2)
    if category_elem:
        metadata["category"] = category_elem.text.strip()
    
    date_selectors = [
        "[data-testid='end-date']",
        "[class*='end-date']",
        "[class*='end']",
        "time",
    ]
    
    for selector in date_selectors:
        date_elem = wait_for_element(driver, By.CSS_SELECTOR, selector, timeout=2)
        if date_elem:
            date_text = date_elem.text.strip()
            if not date_text and selector == "time":
                date_text = date_elem.get_attribute("datetime") or ""
            if date_text and "$" not in date_text and "Vol" not in date_text:
                metadata["end_date"] = date_text
                break
    
    if "end_date" not in metadata:
        date_elems = wait_for_elements(driver, By.CSS_SELECTOR, "[class*='date'], time", timeout=2)
        for date_elem in date_elems:
            date_text = date_elem.text.strip()
            if not date_text:
                date_text = date_elem.get_attribute("datetime") or ""
            if date_text and "$" not in date_text and "Vol" not in date_text and len(date_text) > 5:
                metadata["end_date"] = date_text
                break
    
    resolved_indicators = [
        "Resolved",
        "Settled",
        "Closed",
        "Ended",
    ]
    
    page_text = driver.page_source.lower()
    metadata["resolved"] = any(indicator.lower() in page_text for indicator in resolved_indicators)
    
    return metadata


def extract_market_data_from_network(network_monitor):
    market_data = network_monitor.extract_market_data()
    markets = []
    
    if market_data.get("markets"):
        for market in market_data["markets"]:
            if isinstance(market, dict):
                outcome = market.get("outcome") or market.get("name") or market.get("token")
                price = market.get("price") or market.get("currentPrice") or market.get("lastPrice")
                volume = market.get("volume") or market.get("totalVolume") or 0
                liquidity = market.get("liquidity") or market.get("totalLiquidity") or volume
                
                if outcome and price is not None:
                    markets.append({
                        "outcome": str(outcome),
                        "current_price": float(price) if price > 1 else float(price),
                        "volume": float(volume) if volume else 0.0,
                        "liquidity": float(liquidity) if liquidity else 0.0,
                    })
    
    return markets, market_data.get("price_history", [])


def extract_market_data(driver):
    markets = []
    
    try:
        market_data = driver.execute_script("""
            var markets = [];
            var seenOutcomes = {};
            
            var allElements = document.querySelectorAll('button, [role="button"], div, span');
            
            allElements.forEach(function(elem) {
                var text = elem.textContent || elem.innerText;
                if (!text || text.length < 3 || text.length > 100) return;
                
                text = text.trim();
                
                var outcomeMatch = text.match(/\\b(Up|Down|Yes|No)\\b/i);
                if (!outcomeMatch) return;
                
                var outcome = outcomeMatch[1];
                
                var hasPrice = false;
                var price = null;
                
                var priceMatch = text.match(/([\\d.]+)%/);
                if (priceMatch) {
                    price = parseFloat(priceMatch[1]) / 100;
                    hasPrice = true;
                } else {
                    var numMatch = text.match(/\\b([\\d.]+)\\b/);
                    if (numMatch) {
                        var num = parseFloat(numMatch[1]);
                        if (num > 0 && num <= 1) {
                            price = num;
                            hasPrice = true;
                        } else if (num > 1 && num <= 100) {
                            price = num / 100;
                            hasPrice = true;
                        }
                    }
                }
                
                if (hasPrice && price > 0 && price <= 1) {
                    var key = outcome.toLowerCase();
                    var existing = seenOutcomes[key];
                    if (!existing) {
                        seenOutcomes[key] = {outcome: outcome, price: price, text: text};
                    } else {
                        var priceDiff = Math.abs(existing.price - price);
                        if (priceDiff > 0.01) {
                            if (price > existing.price || (price < 0.5 && existing.price >= 0.5)) {
                                seenOutcomes[key] = {outcome: outcome, price: price, text: text};
                            }
                        }
                    }
                }
            });
            
            for (var key in seenOutcomes) {
                markets.push(seenOutcomes[key]);
            }
            
            return markets;
        """)
        
        if market_data and isinstance(market_data, list):
            seen_outcomes = set()
            for item in market_data:
                if isinstance(item, dict):
                    outcome = item.get("outcome", "").strip()
                    if outcome and outcome not in seen_outcomes:
                        seen_outcomes.add(outcome)
                        market = {
                            "outcome": outcome,
                            "current_price": float(item.get("price", 0.0)),
                            "volume": 0.0,
                            "liquidity": 0.0,
                        }
                        markets.append(market)
    except Exception:
        pass
    
    if not markets:
        outcome_containers = wait_for_elements(driver, By.CSS_SELECTOR, 
            "button, [role='button'], [class*='outcome'], [class*='market'], [class*='option']", timeout=10)
        
        seen_outcomes = set()
        
        for container in outcome_containers[:30]:
            try:
                outcome_text = container.text.strip()
                if not outcome_text or len(outcome_text) < 1:
                    continue
                
                outcome_match = re.match(r'^(Up|Down|Yes|No)\b', outcome_text, re.IGNORECASE)
                if not outcome_match:
                    continue
                
                outcome = outcome_match.group(1)
                if outcome in seen_outcomes:
                    continue
                
                if outcome_text.lower() in ['order', 'market', 'comments', 'hide', 'show', 'more', 'less']:
                    continue
                
                seen_outcomes.add(outcome)
                
                market = {"outcome": outcome}
                
                price_patterns = [
                    r'([\d.]+)%',
                    r'([\d.]+)\s*c',
                ]
                
                price_text = container.text
                price = None
                for pattern in price_patterns:
                    price_match = re.search(pattern, price_text)
                    if price_match:
                        try:
                            price = float(price_match.group(1))
                            if price > 1:
                                price = price / 100
                            break
                        except ValueError:
                            continue
                
                if price is None:
                    num_match = re.search(r'([\d.]+)', price_text)
                    if num_match:
                        try:
                            num = float(num_match.group(1))
                            if 0 < num <= 1:
                                price = num
                            elif 1 < num <= 100:
                                price = num / 100
                        except ValueError:
                            pass
                
                if price is not None:
                    market["current_price"] = price
                else:
                    market["current_price"] = 0.0
                
                volume_patterns = [
                    r'\$([\d,]+)',
                    r'([\d,]+)\s*vol',
                ]
                
                volume = None
                for pattern in volume_patterns:
                    volume_match = re.search(pattern, price_text, re.IGNORECASE)
                    if volume_match:
                        try:
                            volume = float(volume_match.group(1).replace(",", ""))
                            break
                        except ValueError:
                            continue
                
                if volume is not None:
                    market["volume"] = volume
                else:
                    market["volume"] = 0.0
                
                market["liquidity"] = market.get("volume", 0.0)
                
                markets.append(market)
            except Exception:
                continue
    
    if not markets:
        market = {
            "outcome": "Unknown",
            "current_price": 0.0,
            "volume": 0.0,
            "liquidity": 0.0,
        }
        markets.append(market)
    
    return markets


def extract_price_history(driver):
    price_history = []
    
    try:
        chart_data = driver.execute_script("""
            var data = [];
            
            if (window.chartData) {
                data = window.chartData;
            } else if (window.priceData) {
                data = window.priceData;
            } else if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props) {
                var props = window.__NEXT_DATA__.props;
                if (props.pageProps && props.pageProps.priceHistory) {
                    data = props.pageProps.priceHistory;
                } else if (props.initialState && props.initialState.priceHistory) {
                    data = props.initialState.priceHistory;
                }
            }
            
            if (Array.isArray(data)) {
                return data.map(function(point) {
                    return {
                        timestamp: point.timestamp || point.time || point.date || "",
                        price: point.price || point.value || 0.0
                    };
                });
            }
            
            return [];
        """)
        
        if chart_data and isinstance(chart_data, list):
            for point in chart_data:
                if isinstance(point, dict):
                    price_history.append({
                        "timestamp": str(point.get("timestamp", "")),
                        "price": float(point.get("price", 0.0))
                    })
    except Exception:
        pass
    
    try:
        chart_elem = wait_for_element(driver, By.CSS_SELECTOR, "[class*='chart'], svg, canvas", timeout=3)
        if chart_elem:
            tooltip_data = driver.execute_script("""
                var tooltips = document.querySelectorAll('[class*="tooltip"], [class*="hover"]');
                var data = [];
                tooltips.forEach(function(tt) {
                    var text = tt.textContent || tt.innerText;
                    var match = text.match(/(\\d{4}-\\d{2}-\\d{2}[^\\s]*)\\s+([\\d.]+)/);
                    if (match) {
                        data.push({
                            timestamp: match[1],
                            price: parseFloat(match[2])
                        });
                    }
                });
                return data;
            """)
            
            if tooltip_data:
                for point in tooltip_data:
                    price_history.append({
                        "timestamp": str(point.get("timestamp", "")),
                        "price": float(point.get("price", 0.0))
                    })
    except Exception:
        pass
    
    return price_history


def detect_recurring_event(driver):
    past_events_indicators = [
        "Past Events",
        "Previous Events",
        "History",
        "Past Markets",
        "past events",
        "previous events",
    ]
    
    page_text = driver.page_source.lower()
    for indicator in past_events_indicators:
        if indicator.lower() in page_text:
            return True
    
    past_events_link = wait_for_element(driver, By.XPATH, 
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'past') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'previous')]", timeout=2)
    if past_events_link:
        return True
    
    past_events_section = wait_for_element(driver, By.CSS_SELECTOR, 
        "[class*='past'], [class*='previous'], [class*='history'], [data-testid*='past']", timeout=2)
    return past_events_section is not None


def get_past_event_urls(driver, max_events):
    past_event_urls = []
    
    current_url = driver.current_url
    current_event_id = None
    if "/event/" in current_url:
        parts = current_url.split("/event/")
        if len(parts) > 1:
            current_event_id = parts[1].split("?")[0].split("/")[0]
    
    past_events_link = wait_for_element(driver, By.XPATH, 
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'past') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'previous') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'history')]", timeout=5)
    if past_events_link:
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", past_events_link)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", past_events_link)
            time.sleep(4)
        except Exception:
            try:
                past_events_link.click()
                time.sleep(4)
            except Exception:
                pass
    
    for scroll_round in range(3):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
        except Exception:
            break
    
    event_links = wait_for_elements(driver, By.CSS_SELECTOR, "a[href*='/event/']", timeout=10)
    
    seen_urls = set()
    for link in event_links:
        if len(past_event_urls) >= max_events:
            break
        try:
            href = link.get_attribute("href")
            if href and "/event/" in href:
                if not href.startswith("http"):
                    href = "https://polymarket.com" + href
                
                if href not in seen_urls:
                    if current_event_id:
                        event_id = href.split("/event/")[1].split("?")[0].split("/")[0] if "/event/" in href else None
                        if event_id and event_id != current_event_id:
                            past_event_urls.append(href)
                            seen_urls.add(href)
                    else:
                        past_event_urls.append(href)
                        seen_urls.add(href)
        except Exception:
            continue
    
    return past_event_urls

