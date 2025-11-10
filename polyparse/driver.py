from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class NetworkCapture:
    def __init__(self):
        self.responses = defaultdict(list)
        self.requests = defaultdict(list)
    
    def add_response(self, url, response_data):
        self.responses[url].append(response_data)
    
    def add_request(self, url, request_data):
        self.requests[url].append(request_data)
    
    def get_graphql_responses(self):
        graphql_data = []
        for url, responses in self.responses.items():
            if 'graphql' in url.lower() or 'api' in url.lower():
                graphql_data.extend(responses)
        return graphql_data
    
    def get_all_responses(self):
        all_data = []
        for responses in self.responses.values():
            all_data.extend(responses)
        return all_data


def create_driver(headless=False, enable_network_capture=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    if enable_network_capture:
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(5)
        
        if enable_network_capture:
            enable_network_logging(driver)
        
        return driver
    except Exception as e:
        raise WebDriverException(f"Failed to create WebDriver: {e}")


def enable_network_logging(driver):
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Performance.enable", {})
    except Exception:
        pass


def capture_network_responses(driver, timeout=10):
    start_time = time.time()
    captured_responses = []
    
    while time.time() - start_time < timeout:
        try:
            logs = driver.get_log("performance")
            for log in logs:
                message = json.loads(log["message"])
                if message["message"]["method"] == "Network.responseReceived":
                    response = message["message"]["params"]["response"]
                    url = response.get("url", "")
                    if any(keyword in url.lower() for keyword in ["graphql", "api", "polymarket", "event", "market"]):
                        try:
                            response_body = driver.execute_cdp_cmd(
                                "Network.getResponseBody",
                                {"requestId": message["message"]["params"]["requestId"]}
                            )
                            captured_responses.append({
                                "url": url,
                                "body": response_body.get("body", ""),
                                "status": response.get("status", 0)
                            })
                        except Exception:
                            pass
        except Exception:
            pass
        time.sleep(0.5)
    
    return captured_responses


def wait_for_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        return None


def wait_for_elements(driver, by, value, timeout=10):
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, value))
        )
        return elements
    except TimeoutException:
        return []


def safe_click(driver, by, value, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            element = wait_for_element(driver, by, value, timeout)
            if element:
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                element.click()
                return True
        except Exception as e:
            if attempt == retries - 1:
                return False
            time.sleep(1)
    return False


def safe_get_text(driver, by, value, timeout=10, default=""):
    element = wait_for_element(driver, by, value, timeout)
    if element:
        return element.text.strip()
    return default

