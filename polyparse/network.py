import json
import time
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class NetworkMonitor:
    def __init__(self, driver, capture_all=False, url_patterns=None):
        self.driver = driver
        self.responses = []
        self.enabled = False
        self.capture_all = capture_all
        self.url_patterns = url_patterns or [
            r"/api/.*",
            r"/graphql",
            r"/prices?",
            r"/trades?",
            r"polymarket.*event",
            r"polymarket.*market",
        ]
        self.captured_requests = []
        self.payloads = {}
    
    def _want_url(self, url: str) -> bool:
        if self.capture_all:
            return True
        return any(re.search(p, url, re.IGNORECASE) for p in self.url_patterns)
    
    def start(self):
        self.driver.execute_cdp_cmd("Network.enable", {})
        self.enabled = True
    
    def stop(self):
        if self.enabled:
            self.driver.execute_cdp_cmd("Network.disable", {})
            self.enabled = False
    
    def capture_all_responses(self, wait_time=3, scroll_attempts=8):
        if not self.enabled:
            self.start()
        
        time.sleep(1.5)
        
        try:
            logs = self.driver.get_log("performance")
        except Exception:
            logs = []
        
        seen_request_ids = set()
        
        for log in logs:
            try:
                message = json.loads(log["message"])
                method = message.get("message", {}).get("method", "")
                
                if method == "Network.requestWillBeSent":
                    params = message.get("message", {}).get("params", {})
                    request = params.get("request", {})
                    url = request.get("url", "")
                    request_id = params.get("requestId", "")
                    
                    if self._want_url(url) and request_id not in seen_request_ids:
                        self.captured_requests.append((request_id, url))
                        seen_request_ids.add(request_id)
                
                elif method == "Network.responseReceived":
                    params = message.get("message", {}).get("params", {})
                    response = params.get("response", {})
                    url = response.get("url", "")
                    request_id = params.get("requestId", "")
                    
                    if self._want_url(url) and request_id not in seen_request_ids:
                        self.captured_requests.append((request_id, url))
                        seen_request_ids.add(request_id)
                
                elif method == "Network.loadingFinished":
                    params = message.get("message", {}).get("params", {})
                    request_id = params.get("requestId", "")
                    
                    if request_id in [r[0] for r in self.captured_requests]:
                        try:
                            response_body_cmd = self.driver.execute_cdp_cmd(
                                "Network.getResponseBody",
                                {"requestId": request_id}
                            )
                            self.payloads[request_id] = response_body_cmd
                        except Exception:
                            pass
            except Exception:
                continue
        
        time.sleep(wait_time)
        
        for _ in range(scroll_attempts):
            try:
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                
                try:
                    logs = self.driver.get_log("performance")
                    for log in logs:
                        try:
                            message = json.loads(log["message"])
                            method = message.get("message", {}).get("method", "")
                            
                            if method == "Network.loadingFinished":
                                params = message.get("message", {}).get("params", {})
                                request_id = params.get("requestId", "")
                                
                                if request_id not in self.payloads:
                                    try:
                                        response_body_cmd = self.driver.execute_cdp_cmd(
                                            "Network.getResponseBody",
                                            {"requestId": request_id}
                                        )
                                        url = next((r[1] for r in self.captured_requests if r[0] == request_id), "")
                                        if self._want_url(url):
                                            self.payloads[request_id] = response_body_cmd
                                    except Exception:
                                        pass
                        except Exception:
                            continue
                except Exception:
                    pass
            except Exception:
                break
        
        for request_id, url in self.captured_requests:
            if request_id in self.payloads:
                body_data = self.payloads[request_id]
                body = body_data.get("body", "")
                
                self.responses.append({
                    "url": url,
                    "body": body,
                    "requestId": request_id,
                })
        
        return self.responses
    
    def get_responses(self, wait_time=5):
        return self.capture_all_responses(wait_time=wait_time)
    
    def _is_relevant_url(self, url: str) -> bool:
        if not url:
            return False
        
        url_lower = url.lower()
        
        excluded_patterns = [
            ".js",
            ".css",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".woff",
            ".ttf",
            ".ico",
            "google-analytics",
            "googleapis.com/analytics",
            "facebook.net",
            "doubleclick",
            "googletagmanager",
            "gstatic",
        ]
        
        if any(pattern in url_lower for pattern in excluded_patterns):
            return False
        
        relevant_keywords = [
            "graphql",
            "api",
            "polymarket",
            "event",
            "market",
            "price",
            "history",
            "data",
            "query",
            "subscription",
        ]
        
        if any(keyword in url_lower for keyword in relevant_keywords):
            return True
        
        if "polymarket.com" in url_lower:
            return True
        
        return False
    
    def extract_market_data(self) -> Dict[str, Any]:
        market_data = {
            "event": None,
            "markets": [],
            "price_history": [],
            "raw_responses": [],
        }
        
        for response in self.responses:
            try:
                body = response.get("body", "")
                if not body:
                    continue
                
                url = response.get("url", "")
                content_type = response.get("headers", {}).get("content-type", "")
                
                if "json" in content_type.lower() or "graphql" in url.lower() or "api" in url.lower():
                    try:
                        data = json.loads(body)
                        market_data["raw_responses"].append({
                            "url": url,
                            "data": data
                        })
                        market_data = self._parse_json_response(data, market_data)
                    except json.JSONDecodeError:
                        try:
                            if body.strip().startswith("{") or body.strip().startswith("["):
                                data = json.loads(body)
                                market_data["raw_responses"].append({
                                    "url": url,
                                    "data": data
                                })
                                market_data = self._parse_json_response(data, market_data)
                        except:
                            pass
            except Exception:
                continue
        
        return market_data
    
    def _parse_json_response(self, data: Any, market_data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict):
            if "data" in data:
                nested_data = data["data"]
                if isinstance(nested_data, dict):
                    market_data = self._parse_json_response(nested_data, market_data)
            
            if isinstance(data, dict):
                if "event" in data or "market" in data or "getEvent" in str(data.keys()):
                    event_data = data.get("event") or data.get("market") or data.get("getEvent") or data
                    if isinstance(event_data, dict):
                        if not market_data["event"] or not isinstance(market_data["event"], dict):
                            market_data["event"] = event_data
                        else:
                            market_data["event"].update(event_data)
                
                if "markets" in data or "market" in data:
                    markets = data.get("markets") or []
                    if isinstance(data.get("market"), dict):
                        markets = [data["market"]]
                    if isinstance(markets, list):
                        market_data["markets"].extend(markets)
                
                if "outcomes" in data:
                    outcomes = data["outcomes"]
                    if isinstance(outcomes, list):
                        for outcome in outcomes:
                            if isinstance(outcome, dict):
                                market_data["markets"].append(outcome)
                
                if "tokens" in data:
                    tokens = data["tokens"]
                    if isinstance(tokens, list):
                        market_data["markets"].extend(tokens)
                
                history_keys = ["priceHistory", "price_history", "history", "priceData", "timeSeries", "candles", "ticks"]
                for key in history_keys:
                    if key in data:
                        history = data[key]
                        if isinstance(history, list):
                            market_data["price_history"].extend(history)
                
                if "price" in data and isinstance(data["price"], list):
                    market_data["price_history"].extend(data["price"])
                
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        market_data = self._parse_json_response(value, market_data)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if "outcome" in item or "token" in item or "price" in item:
                        market_data["markets"].append(item)
                    elif "timestamp" in item or "time" in item or "date" in item:
                        market_data["price_history"].append(item)
                    else:
                        market_data = self._parse_json_response(item, market_data)
        
        return market_data
    
    def get_graphql_queries(self) -> List[Dict[str, Any]]:
        graphql_responses = []
        for response in self.responses:
            url = response.get("url", "")
            if "graphql" in url.lower():
                try:
                    body = response.get("body", "")
                    if body:
                        data = json.loads(body)
                        graphql_responses.append({
                            "url": url,
                            "data": data
                        })
                except Exception:
                    pass
        return graphql_responses

