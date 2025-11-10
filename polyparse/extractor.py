from datetime import datetime
import time
import json
from .parser import (
    navigate_to_event,
    extract_event_metadata,
    extract_market_data,
    extract_price_history,
    detect_recurring_event,
    get_past_event_urls,
    extract_market_data_from_network,
)
from .network import NetworkMonitor
from .utils import extract_event_id_from_url, extract_slug_from_url


def extract_event_data(driver, url, use_network=True, capture_dir=None, fast_mode=False):
    network_monitor = None
    if use_network:
        network_monitor = NetworkMonitor(driver, capture_all=True)
        network_monitor.start()
    
    navigate_to_event(driver, url, fast_mode=fast_mode)
    
    if network_monitor:
        if fast_mode:
            time.sleep(1)
            all_responses = network_monitor.capture_all_responses(wait_time=2, scroll_attempts=5)
        else:
            time.sleep(2)
            all_responses = network_monitor.capture_all_responses(wait_time=3, scroll_attempts=8)
        
        if capture_dir:
            from pathlib import Path
            import re
            capture_path = Path(capture_dir)
            capture_path.mkdir(exist_ok=True)
            
            for response in all_responses:
                url_val = response.get("url", "")
                body = response.get("body", "")
                if not body:
                    continue
                
                base = re.sub(r"[^a-zA-Z0-9._-]+", "_", url_val[-120:])
                if len(base) > 100:
                    base = base[:100]
                fpath = capture_path / f"{base}.json"
                
                counter = 1
                while fpath.exists():
                    fpath = capture_path / f"{base}_{counter}.json"
                    counter += 1
                
                try:
                    with open(fpath, "w", encoding="utf-8") as f:
                        try:
                            parsed = json.loads(body)
                            json.dump(parsed, f, ensure_ascii=False, indent=2)
                        except Exception:
                            f.write(body)
                except Exception:
                    pass
    
    event_data = {
        "event_id": extract_event_id_from_url(url) or extract_slug_from_url(url) or "unknown",
        "url": url,
        "scraped_at": datetime.utcnow().isoformat() + "Z",
    }
    
    metadata = extract_event_metadata(driver)
    event_data.update(metadata)
    
    markets = []
    price_history = []
    
    if network_monitor:
        try:
            all_responses = network_monitor.get_responses(wait_time=3)
            graphql_responses = network_monitor.get_graphql_queries()
            
            for response in network_monitor.responses:
                try:
                    body = response.get("body", "")
                    if not body:
                        continue
                    
                    url = response.get("url", "")
                    if "graphql" in url.lower() or "api" in url.lower():
                        try:
                            data = json.loads(body)
                            graphql_responses.append({"url": url, "data": data})
                        except:
                            pass
                except:
                    pass
            
            extracted_data = network_monitor.extract_market_data()
            
            for response in network_monitor.responses:
                try:
                    body = response.get("body", "")
                    url_val = response.get("url", "")
                    if not body:
                        continue
                    
                    try:
                        data = json.loads(body)
                    except:
                        continue
                    
                    if isinstance(data, dict):
                        if "openPrice" in data or "closePrice" in data or "timestamp" in data:
                            if "crypto-price" in url_val.lower() or "price" in url_val.lower():
                                timestamp = data.get("timestamp") or data.get("time") or data.get("t")
                                open_price = data.get("openPrice") or data.get("open") or data.get("price")
                                close_price = data.get("closePrice") or data.get("close") or data.get("price")
                                
                                if timestamp:
                                    if open_price:
                                        price_history.append({
                                            "timestamp": str(timestamp),
                                            "price": float(open_price)
                                        })
                                    if close_price and close_price != open_price:
                                        price_history.append({
                                            "timestamp": str(timestamp),
                                            "price": float(close_price)
                                        })
                        
                        if "pageProps" in data:
                            page_props = data["pageProps"]
                            if isinstance(page_props, dict):
                                if "dehydratedState" in page_props:
                                    dehydrated = page_props["dehydratedState"]
                                    if isinstance(dehydrated, dict) and "queries" in dehydrated:
                                        for query in dehydrated["queries"]:
                                            if isinstance(query, dict) and "state" in query:
                                                query_state = query["state"]
                                                if isinstance(query_state, dict) and "data" in query_state:
                                                    query_data = query_state["data"]
                                                    if isinstance(query_data, dict):
                                                        if "event" in query_data or "market" in query_data:
                                                            event_info = query_data.get("event") or query_data.get("market") or query_data
                                                            if isinstance(event_info, dict):
                                                                if not event_data.get("title") and event_info.get("title"):
                                                                    event_data["title"] = event_info["title"]
                                                                if not event_data.get("description") and event_info.get("description"):
                                                                    event_data["description"] = event_info["description"]
                                                                if event_info.get("endDate") or event_info.get("end_date"):
                                                                    event_data["end_date"] = str(event_info.get("endDate") or event_info.get("end_date", ""))
                                                                if event_info.get("resolved") is not None:
                                                                    event_data["resolved"] = event_info["resolved"]
                                                        
                                                        if "markets" in query_data:
                                                            markets_list = query_data["markets"]
                                                            if isinstance(markets_list, list):
                                                                for market in markets_list:
                                                                    if isinstance(market, dict):
                                                                        outcomes = market.get("outcomes", [])
                                                                        outcome_prices = market.get("outcomePrices", [])
                                                                        volume = market.get("volume") or market.get("volumeNum") or market.get("volume_num") or 0
                                                                        liquidity = market.get("liquidity") or market.get("liquidityNum") or market.get("liquidity_num") or volume

                                                                        # Get the market identifier (candidate name, etc.)
                                                                        market_name = (market.get("title") or market.get("question") or
                                                                                     market.get("groupItemTitle") or market.get("token") or
                                                                                     market.get("ticker") or market.get("name") or
                                                                                     market.get("description", ""))

                                                                        for idx, outcome in enumerate(outcomes):
                                                                            if idx < len(outcome_prices):
                                                                                try:
                                                                                    price = float(outcome_prices[idx])
                                                                                    if price > 1:
                                                                                        price = price / 100

                                                                                    # For multi-candidate markets, prepend candidate name to outcome
                                                                                    outcome_label = str(outcome)
                                                                                    if market_name and len(outcomes) > 1 and len(markets_list) > 1:
                                                                                        # If there are multiple markets with Yes/No outcomes, prefix with market name
                                                                                        if outcome_label in ["Yes", "No", "Up", "Down"]:
                                                                                            outcome_label = f"{market_name}"

                                                                                    market_obj = {
                                                                                        "outcome": outcome_label,
                                                                                        "current_price": price,
                                                                                        "volume": float(volume) if volume else 0.0,
                                                                                        "liquidity": float(liquidity) if liquidity else 0.0,
                                                                                        "price_history": [],
                                                                                    }
                                                                                    
                                                                                    if market.get("priceHistory") or market.get("history"):
                                                                                        history = market.get("priceHistory") or market.get("history")
                                                                                        if isinstance(history, list):
                                                                                            market_obj["price_history"] = [
                                                                                                {
                                                                                                    "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date") or h.get("t", "")),
                                                                                                    "price": float(h.get("price") or h.get("value") or h.get("close") or h.get("p", 0))
                                                                                                }
                                                                                                for h in history if isinstance(h, dict)
                                                                                            ]
                                                                                    
                                                                                    markets.append(market_obj)
                                                                                except:
                                                                                    pass
                                        
                                                        if isinstance(query_data, list):
                                                            for item in query_data:
                                                                if isinstance(item, dict):
                                                                    if "markets" in item:
                                                                        markets_list = item["markets"]
                                                                        if isinstance(markets_list, list):
                                                                            for market in markets_list:
                                                                                if isinstance(market, dict):
                                                                                    outcomes = market.get("outcomes", [])
                                                                                    outcome_prices = market.get("outcomePrices", [])
                                                                                    volume = market.get("volume") or market.get("volumeNum") or market.get("volume_num") or 0
                                                                                    liquidity = market.get("liquidity") or market.get("liquidityNum") or market.get("liquidity_num") or volume

                                                                                    # Get the market identifier (candidate name, etc.)
                                                                                    market_name = (market.get("title") or market.get("question") or
                                                                                                 market.get("groupItemTitle") or market.get("token") or
                                                                                                 market.get("ticker") or market.get("name") or
                                                                                                 market.get("description", ""))

                                                                                    for idx, outcome in enumerate(outcomes):
                                                                                        if idx < len(outcome_prices):
                                                                                            try:
                                                                                                price = float(outcome_prices[idx])
                                                                                                if price > 1:
                                                                                                    price = price / 100

                                                                                                # For multi-candidate markets, prepend candidate name to outcome
                                                                                                outcome_label = str(outcome)
                                                                                                if market_name and len(outcomes) > 1 and len(markets_list) > 1:
                                                                                                    # If there are multiple markets with Yes/No outcomes, prefix with market name
                                                                                                    if outcome_label in ["Yes", "No", "Up", "Down"]:
                                                                                                        outcome_label = f"{market_name}"

                                                                                                market_obj = {
                                                                                                    "outcome": outcome_label,
                                                                                                    "current_price": price,
                                                                                                    "volume": float(volume) if volume else 0.0,
                                                                                                    "liquidity": float(liquidity) if liquidity else 0.0,
                                                                                                    "price_history": [],
                                                                                                }
                                                                                                
                                                                                                if market.get("priceHistory") or market.get("history"):
                                                                                                    history = market.get("priceHistory") or market.get("history")
                                                                                                    if isinstance(history, list):
                                                                                                        market_obj["price_history"] = [
                                                                                                            {
                                                                                                                "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date") or h.get("t", "")),
                                                                                                                "price": float(h.get("price") or h.get("value") or h.get("close") or h.get("p", 0))
                                                                                                            }
                                                                                                            for h in history if isinstance(h, dict)
                                                                                                        ]
                                                                                                
                                                                                                markets.append(market_obj)
                                                                                            except:
                                                                                                pass
                except Exception as e:
                    pass
            
            if extracted_data.get("event"):
                event_info = extracted_data["event"]
                if isinstance(event_info, dict):
                    if not event_data.get("title") and event_info.get("title"):
                        event_data["title"] = event_info["title"]
                    if not event_data.get("description") and event_info.get("description"):
                        event_data["description"] = event_info["description"]
                    if event_info.get("endDate") or event_info.get("end_date"):
                        event_data["end_date"] = event_info.get("endDate") or event_info.get("end_date")
                    if event_info.get("resolved") is not None:
                        event_data["resolved"] = event_info["resolved"]
            
            all_markets = extracted_data.get("markets", [])
            all_price_history = extracted_data.get("price_history", [])
            
            for market in all_markets:
                if not isinstance(market, dict):
                    continue
                
                outcome = (market.get("outcome") or market.get("token") or 
                          market.get("name") or market.get("side") or 
                          market.get("label"))
                
                if not outcome:
                    continue
                
                price = (market.get("price") or market.get("currentPrice") or 
                        market.get("lastPrice") or market.get("latestPrice") or
                        market.get("yesPrice") or market.get("noPrice"))
                
                if price is None:
                    price_str = market.get("priceDisplay") or market.get("priceStr")
                    if price_str:
                        try:
                            price = float(price_str.replace("%", "").replace("$", "").strip())
                            if price > 1:
                                price = price / 100
                        except:
                            pass
                
                if price is None:
                    continue
                
                volume = (market.get("volume") or market.get("totalVolume") or 
                         market.get("volume24h") or market.get("volumeUsd") or 0)
                
                liquidity = (market.get("liquidity") or market.get("totalLiquidity") or
                            market.get("liquidityUsd") or volume)
                
                market_obj = {
                    "outcome": str(outcome),
                    "current_price": float(price) if price <= 1 else float(price) / 100,
                    "volume": float(volume) if volume else 0.0,
                    "liquidity": float(liquidity) if liquidity else 0.0,
                }
                
                market_history = (market.get("priceHistory") or market.get("history") or
                                 market.get("priceData") or market.get("timeSeries") or
                                 market.get("candles") or market.get("ticks") or [])
                
                if isinstance(market_history, list) and market_history:
                    market_obj["price_history"] = [
                        {
                            "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date") or h.get("t", "")),
                            "price": float(h.get("price") or h.get("value") or h.get("close") or h.get("p", 0))
                        }
                        for h in market_history if isinstance(h, dict)
                    ]
                else:
                    market_obj["price_history"] = []
                
                markets.append(market_obj)
            
            if all_price_history and isinstance(all_price_history, list):
                price_history = [
                    {
                        "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date") or h.get("t", "")),
                        "price": float(h.get("price") or h.get("value") or h.get("close") or h.get("p", 0))
                    }
                    for h in all_price_history if isinstance(h, dict)
                ]
            
            for response in graphql_responses:
                data = response.get("data", {})
                if isinstance(data, dict):
                    if "data" in data:
                        data = data["data"]
                    
                    if isinstance(data, dict):
                        if "event" in data:
                            event_info = data["event"]
                            if isinstance(event_info, dict):
                                if not event_data.get("title") and event_info.get("title"):
                                    event_data["title"] = event_info["title"]
                                if not event_data.get("description") and event_info.get("description"):
                                    event_data["description"] = event_info["description"]
                        
                        if "markets" in data or "outcomes" in data or "tokens" in data:
                            market_list = data.get("markets") or data.get("outcomes") or data.get("tokens") or []
                            for market in market_list:
                                if isinstance(market, dict):
                                    outcome = market.get("outcome") or market.get("token") or market.get("name")
                                    price = market.get("price") or market.get("currentPrice") or market.get("lastPrice")
                                    
                                    if outcome and price is not None:
                                        existing_market = next((m for m in markets if m["outcome"] == str(outcome)), None)
                                        if existing_market:
                                            if not existing_market.get("price_history") and (market.get("priceHistory") or market.get("history")):
                                                history = market.get("priceHistory") or market.get("history")
                                                if isinstance(history, list):
                                                    existing_market["price_history"] = [
                                                        {
                                                            "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date", "")),
                                                            "price": float(h.get("price") or h.get("value", 0))
                                                        }
                                                        for h in history
                                                    ]
                                        else:
                                            market_obj = {
                                                "outcome": str(outcome),
                                                "current_price": float(price) if price <= 1 else float(price) / 100,
                                                "volume": float(market.get("volume", 0) or market.get("totalVolume", 0) or 0),
                                                "liquidity": float(market.get("liquidity", 0) or market.get("totalLiquidity", 0) or 0),
                                            }
                                            
                                            if market.get("priceHistory") or market.get("history"):
                                                history = market.get("priceHistory") or market.get("history")
                                                if isinstance(history, list):
                                                    market_obj["price_history"] = [
                                                        {
                                                            "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date", "")),
                                                            "price": float(h.get("price") or h.get("value", 0))
                                                        }
                                                        for h in history
                                                    ]
                                                else:
                                                    market_obj["price_history"] = []
                                            else:
                                                market_obj["price_history"] = []
                                            
                                            markets.append(market_obj)
                        
                        if "priceHistory" in data or "history" in data or "priceData" in data:
                            history = data.get("priceHistory") or data.get("history") or data.get("priceData")
                            if isinstance(history, list):
                                price_history.extend([
                                    {
                                        "timestamp": str(h.get("timestamp") or h.get("time") or h.get("date", "")),
                                        "price": float(h.get("price") or h.get("value", 0))
                                    }
                                    for h in history if isinstance(h, dict)
                                ])
        except Exception as e:
            pass
        
        if network_monitor:
            network_monitor.stop()
    
    if not markets:
        markets = extract_market_data(driver)
        price_history = extract_price_history(driver)
    
    seen_markets = {}
    for market in markets:
        outcome = market.get("outcome", "")
        key = f"{outcome}_{market.get('current_price', 0)}"
        
        if key not in seen_markets:
            seen_markets[key] = market
        else:
            existing = seen_markets[key]
            if market.get("volume", 0) > existing.get("volume", 0):
                seen_markets[key] = market
            if market.get("price_history") and len(market["price_history"]) > len(existing.get("price_history", [])):
                existing["price_history"] = market["price_history"]
    
    markets = list(seen_markets.values())
    
    for market in markets:
        if "price_history" not in market or not market["price_history"]:
            if price_history:
                market["price_history"] = price_history.copy()
            else:
                market["price_history"] = []
        
        if market["price_history"]:
            market["price_history"] = sorted(market["price_history"], 
                                            key=lambda x: int(x.get("timestamp", 0)) if str(x.get("timestamp", "")).isdigit() else x.get("timestamp", ""))
    
    event_data["markets"] = markets
    
    return event_data


def extract_recurring_events(driver, url, num_past_events, capture_dir=None):
    main_event_data = extract_event_data(driver, url, capture_dir=capture_dir)
    
    is_recurring = detect_recurring_event(driver)
    
    if not is_recurring and num_past_events > 0:
        for scroll_round in range(3):
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
            except Exception:
                break
        is_recurring = detect_recurring_event(driver)
    
    if not is_recurring:
        main_event_data["past_events"] = []
        return main_event_data
    
    past_event_urls = get_past_event_urls(driver, num_past_events)
    
    if not past_event_urls:
        main_event_data["past_events"] = []
        return main_event_data
    
    past_events = []
    for i, past_url in enumerate(past_event_urls, 1):
        try:
            past_event = extract_event_data(driver, past_url, use_network=True, capture_dir=None, fast_mode=True)
            past_events.append(past_event)
        except Exception as e:
            continue
    
    main_event_data["past_events"] = past_events
    
    return main_event_data

