"""
Screener.in Web Scraper Module
Handles all Selenium-based data scraping from Screener.in
"""

import os
import re
import time
import traceback
from threading import Lock
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService

# Configuration
import os
SCREENER_USERNAME = os.environ.get('SCREENER_USERNAME', 'your_username')
SCREENER_PASSWORD = os.environ.get('SCREENER_PASSWORD', 'your_password')
EDGE_DRIVER_PATH = os.environ.get('EDGE_DRIVER_PATH', r'D:\StockDash\msedgedriver.exe')


# Thread synchronization
selenium_lock = Lock()

def scrape_screener_ratios(ticker):
    """
    Scrape fresh financial ratios from Screener.in using Selenium
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AXISBANK')
        
    Returns:
        dict: Financial ratios data or None if failed
    """
    print(f"🔄 [SCRAPER] Starting scrape for {ticker}")
    
    with selenium_lock:
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--guest')
        options.add_argument('--no-first-run')
        
        if not os.path.exists(EDGE_DRIVER_PATH):
            print(f"❌ [SCRAPER] EdgeDriver not found at {EDGE_DRIVER_PATH}")
            return None
        
        driver = None
        try:
            # Initialize webdriver
            service = EdgeService(EDGE_DRIVER_PATH)
            driver = webdriver.Edge(service=service, options=options)
            wait = WebDriverWait(driver, 15)
            
            # Login to Screener.in
            print(f"🔐 [SCRAPER] Logging into Screener.in...")
            driver.get('https://www.screener.in/login/')
            time.sleep(2)
            
            # Fill login form
            username_input = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
            username_input.clear()
            username_input.send_keys(SCREENER_USERNAME)
            
            password_input = driver.find_element(By.NAME, 'password')
            password_input.clear()
            password_input.send_keys(SCREENER_PASSWORD)
            
            # Submit login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Verify login success
            time.sleep(5)
            if '/login/' in driver.current_url:
                print(f"❌ [SCRAPER] Login failed for {ticker}")
                _log_login_errors(driver)
                return None
            
            print(f"✅ [SCRAPER] Login successful")
            
            # Navigate to company page
            ticker_url = f'https://www.screener.in/company/{ticker}/consolidated/'
            print(f"📊 [SCRAPER] Navigating to {ticker} page...")
            driver.get(ticker_url)
            
            # Wait for ratios section to load
            wait.until(EC.presence_of_element_located((By.ID, 'top-ratios')))
            time.sleep(3)
            
            # Parse ratios data
            ratios = _parse_ratios_from_page(driver, ticker)
            
            if ratios:
                print(f"✅ [SCRAPER] Successfully scraped {len(ratios)} ratios for {ticker}")
                return ratios
            else:
                print(f"❌ [SCRAPER] No ratios found for {ticker}")
                _save_debug_page(driver, ticker)
                return None
                
        except Exception as e:
            print(f"❌ [SCRAPER] Exception for {ticker}: {str(e)}")
            print(f"❌ [SCRAPER] Traceback: {traceback.format_exc()}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                    print(f"🚫 [SCRAPER] Browser closed")
                except Exception:
                    pass

def _log_login_errors(driver):
    """Log login error messages for debugging"""
    try:
        error_elements = driver.find_elements(By.CLASS_NAME, 'error')
        for error in error_elements:
            print(f"🚨 [SCRAPER] Login error: {error.text}")
    except Exception:
        pass

def _parse_ratios_from_page(driver, ticker):
    """Parse financial ratios from the loaded page - Enhanced Version"""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        top_ratios = soup.find('ul', id='top-ratios')
        
        if not top_ratios:
            print(f"❌ [SCRAPER] Ratios section not found for {ticker}")
            return None
        
        # Get ALL ratio items (both default and quick-ratio)
        ratio_items = top_ratios.find_all('li', class_='flex flex-space-between')
        ratios = {}
        
        print(f"🔍 [SCRAPER] Found {len(ratio_items)} total ratios for {ticker}")
        
        for item in ratio_items:
            name_span = item.find('span', class_='name')
            value_span = item.find('span', class_='value')
            
            if name_span and value_span:
                ratio_name = name_span.get_text(strip=True)
                full_value = value_span.get_text(strip=True)
                
                # Extract number value more robustly
                number_spans = value_span.find_all('span', class_='number')
                if number_spans:
                    # Handle cases like "High / Low" with multiple numbers
                    number_values = [span.get_text(strip=True) for span in number_spans]
                    if len(number_values) == 1:
                        number_value = number_values[0]
                    else:
                        number_value = ' / '.join(number_values)
                else:
                    number_value = ""
                
                # Extract unit by removing number values from full value
                unit = full_value
                for num in number_values if number_spans else []:
                    unit = unit.replace(num, '')
                unit = re.sub(r'[₹\s/]+', ' ', unit).strip()
                
                # Get data source type
                data_source = item.get('data-source', 'unknown')
                
                ratios[ratio_name] = {
                    'full_value': full_value,
                    'number_value': number_value,
                    'unit': unit,
                    'source_type': data_source  # Added for debugging
                }
                
                print(f"   ✓ {ratio_name}: {full_value} (source: {data_source})")
        
        print(f"✅ [SCRAPER] Successfully parsed {len(ratios)} ratios")
        return ratios if ratios else None
        
    except Exception as e:
        print(f"❌ [SCRAPER] Error parsing ratios: {e}")
        print(f"❌ [SCRAPER] Traceback: {traceback.format_exc()}")
        return None


def _save_debug_page(driver, ticker):
    """Save page source for debugging purposes"""
    try:
        with open(f'debug_scraper_{ticker}.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"💾 [SCRAPER] Debug page saved: debug_scraper_{ticker}.html")
    except Exception as e:
        print(f"❌ [SCRAPER] Could not save debug page: {e}")

def test_scraper(ticker='AXISBANK'):
    """Test function to verify scraper is working"""
    print(f"🧪 [SCRAPER] Testing scraper with {ticker}")
    result = scrape_screener_ratios(ticker)
    
    if result:
        print(f"✅ [SCRAPER] Test successful! Found {len(result)} ratios")
        for name, data in list(result.items())[:3]:  # Show first 3 ratios
            print(f"   {name}: {data['full_value']}")
    else:
        print(f"❌ [SCRAPER] Test failed!")
    
    return result



def scrape_quarterly_results(ticker):
    """
    Scrape quarterly financial results from Screener.in
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Quarterly results data with headers and rows
    """
    print(f"📊 [SCRAPER] Scraping quarterly results for {ticker}")
    
    with selenium_lock:
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--guest')
        options.add_argument('--no-first-run')
        
        if not os.path.exists(EDGE_DRIVER_PATH):
            print(f"❌ [SCRAPER] EdgeDriver not found at {EDGE_DRIVER_PATH}")
            return None
        
        driver = None
        try:
            # Initialize webdriver
            service = EdgeService(EDGE_DRIVER_PATH)
            driver = webdriver.Edge(service=service, options=options)
            wait = WebDriverWait(driver, 15)
            
            # Login to Screener.in
            print(f"🔐 [SCRAPER] Logging into Screener.in...")
            driver.get('https://www.screener.in/login/')
            time.sleep(2)
            
            # Fill login form
            username_input = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
            username_input.clear()
            username_input.send_keys(SCREENER_USERNAME)
            
            password_input = driver.find_element(By.NAME, 'password')
            password_input.clear()
            password_input.send_keys(SCREENER_PASSWORD)
            
            # Submit login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Verify login success
            time.sleep(5)
            if '/login/' in driver.current_url:
                print(f"❌ [SCRAPER] Login failed for {ticker}")
                _log_login_errors(driver)
                return None
            
            print(f"✅ [SCRAPER] Login successful")
            
            # Navigate to company page
            ticker_url = f'https://www.screener.in/company/{ticker}/consolidated/'
            print(f"📊 [SCRAPER] Navigating to {ticker} page...")
            driver.get(ticker_url)
            
            # Wait for quarterly results section
            wait.until(EC.presence_of_element_located((By.ID, 'quarters')))
            time.sleep(3)
            
            # Parse quarterly data
            quarterly_data = _parse_quarterly_results(driver, ticker)
            
            if quarterly_data:
                print(f"✅ [SCRAPER] Successfully scraped quarterly data for {ticker}")
                return quarterly_data
            else:
                print(f"❌ [SCRAPER] No quarterly data found for {ticker}")
                return None
                
        except Exception as e:
            print(f"❌ [SCRAPER] Exception in quarterly scraping: {str(e)}")
            print(f"❌ [SCRAPER] Traceback: {traceback.format_exc()}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                    print(f"🚫 [SCRAPER] Browser closed")
                except Exception:
                    pass


def _parse_quarterly_results(driver, ticker):
    """Parse quarterly results table from the page"""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        quarters_section = soup.find('section', id='quarters')
        
        if not quarters_section:
            print(f"❌ [SCRAPER] Quarterly section not found for {ticker}")
            return None
        
        # Find the data table
        table = quarters_section.find('table', class_='data-table')
        if not table:
            print(f"❌ [SCRAPER] Quarterly table not found for {ticker}")
            return None
        
        # Extract headers (quarters)
        headers = []
        header_row = table.find('thead').find('tr')
        for th in header_row.find_all('th')[1:]:  # Skip first empty header
            quarter = th.get_text(strip=True)
            if quarter:
                headers.append(quarter)
        
        # Extract data rows
        quarterly_data = {
            'headers': headers,
            'metrics': {}
        }
        
        tbody = table.find('tbody')
        for row in tbody.find_all('tr'):
            if 'font-size-14' in row.get('class', []):  # Skip PDF links row
                continue
                
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
                
            # Get metric name
            metric_name = cells[0].get_text(strip=True)
            # Clean metric name (remove + buttons)
            metric_name = re.sub(r'\s*\+\s*$', '', metric_name)
            
            # Get values for each quarter
            values = []
            for cell in cells[1:len(headers)+1]:  # Match header count
                value = cell.get_text(strip=True)
                values.append(value)
            
            quarterly_data['metrics'][metric_name] = values
            print(f"   ✓ {metric_name}: {len(values)} quarters")
        
        print(f"✅ [SCRAPER] Parsed {len(quarterly_data['metrics'])} metrics across {len(headers)} quarters")
        return quarterly_data
        
    except Exception as e:
        print(f"❌ [SCRAPER] Error parsing quarterly results: {e}")
        print(f"❌ [SCRAPER] Traceback: {traceback.format_exc()}")
        return None


if __name__ == '__main__':
    # Test the scraper directly
    test_scraper()
