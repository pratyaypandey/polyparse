import json
import re
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def capture_all_network_data(url: str, output_dir: str = "./captures", url_patterns: List[str] = None, headless: bool = True):
    if url_patterns is None:
        url_patterns = [
            r"/api/.*",
            r"/graphql",
            r"/prices?",
            r"/trades?",
            r"polymarket.*event",
            r"polymarket.*market",
            r".*polymarket.*",
        ]
    
    outdir = Path(output_dir)
    outdir.mkdir(exist_ok=True)
    
    def want(url: str) -> bool:
        if not url:
            return False
        excluded = [".js", ".css", ".png", ".jpg", ".svg", ".woff", ".ttf", ".ico", "google", "facebook", "analytics"]
        if any(pattern in url.lower() for pattern in excluded):
            return False
        return any(re.search(p, url, re.IGNORECASE) for p in url_patterns)
    
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        
        captured = []
        payloads = {}
        
        driver.get(url)
        time.sleep(4)
        
        last_height = 0
        for scroll_round in range(15):
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2.0)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            except Exception:
                break
        
        time.sleep(3)
        
        try:
            logs = driver.get_log("performance")
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
                    url_val = request.get("url", "")
                    request_id = params.get("requestId", "")
                    
                    if want(url_val) and request_id not in seen_request_ids:
                        captured.append((request_id, url_val))
                        seen_request_ids.add(request_id)
                
                elif method == "Network.loadingFinished":
                    params = message.get("message", {}).get("params", {})
                    request_id = params.get("requestId", "")
                    
                    if request_id in [c[0] for c in captured]:
                        try:
                            body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                            payloads[request_id] = body
                        except Exception:
                            pass
            except Exception:
                continue
        
        index = []
        
        for req_id, url_val in captured:
            body_data = payloads.get(req_id)
            if not body_data:
                continue
            
            text = body_data.get("body", "")
            if not text:
                continue
            
            base = re.sub(r"[^a-zA-Z0-9._-]+", "_", url_val[-120:])
            if len(base) > 100:
                base = base[:100]
            fpath = outdir / f"{base}.json"
            
            counter = 1
            while fpath.exists():
                fpath = outdir / f"{base}_{counter}.json"
                counter += 1
            
            with open(fpath, "w", encoding="utf-8") as f:
                try:
                    parsed = json.loads(text)
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                except Exception:
                    f.write(text)
            
            index.append({
                "requestId": req_id,
                "url": url_val,
                "file": str(fpath),
                "size": len(text)
            })
        
        with open(outdir / "index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        
        return index
    
    finally:
        driver.quit()


