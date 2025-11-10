import getpass
from selenium.webdriver.common.by import By
from .driver import wait_for_element, safe_click, safe_get_text
import time


def login(driver, email=None, password=None):
    if not email:
        email = input("Enter your Polymarket email: ")
    if not password:
        password = getpass.getpass("Enter your Polymarket password: ")
    
    driver.get("https://polymarket.com/login")
    time.sleep(2)
    
    email_input = wait_for_element(driver, By.NAME, "email", timeout=10)
    if not email_input:
        email_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[type="email"]', timeout=10)
    
    if email_input:
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(0.5)
    
    password_input = wait_for_element(driver, By.NAME, "password", timeout=10)
    if not password_input:
        password_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[type="password"]', timeout=10)
    
    if password_input:
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(0.5)
    
    login_button = wait_for_element(driver, By.CSS_SELECTOR, 'button[type="submit"]', timeout=10)
    if not login_button:
        login_button = wait_for_element(driver, By.XPATH, "//button[contains(text(), 'Sign') or contains(text(), 'Log')]", timeout=10)
    
    if login_button:
        safe_click(driver, By.CSS_SELECTOR, 'button[type="submit"]', timeout=5)
        time.sleep(3)
        
        if "login" not in driver.current_url.lower():
            return True
    
    return False


