"""
Stock Portfolio Management API
A Flask-based backend for managing stock portfolios with SQLite database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper import scrape_screener_ratios, scrape_quarterly_results
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
import traceback
from datetime import datetime
from auth import register_user, login_user, jwt_required, get_current_user

# Import database functions
from database import (
    init_database, get_or_create_company, create_holding, add_purchase,
    get_all_holdings, get_holding_by_id, update_holding_prices, 
    sell_holding_shares, save_ratios_cache, get_ratios_cache,
    save_quarterly_cache, get_quarterly_cache, get_companies_for_suggestions,
    find_company_by_ticker, update_holding_avg_price_and_quantity,
    find_existing_holding_by_ticker
)

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_database()
print("🗄️ SQLite database initialized")

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user account"""
    try:
        data = request.get_json() or {}
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        result = register_user(username, email, password, first_name, last_name)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'message': result['message'],
            'user': {
                'id': result['user_id'],
                'username': result['username'],
                'email': result['email']
            },
            'token': result['token']
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json() or {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        result = login_user(username, password)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 401
        
        return jsonify({
            'message': result['message'],
            'user': {
                'id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'first_name': result['first_name'],
                'last_name': result['last_name']
            },
            'token': result['token']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/profile', methods=['GET'])
@jwt_required
def get_profile():
    """Get current user profile"""
    try:
        current_user = get_current_user()
        user_id = current_user['user_id']
        
        # Get full user details from database
        from database import get_user_by_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'created_at': user['created_at']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Profile fetch failed: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
@jwt_required
def logout():
    """User logout endpoint (client-side token removal)"""
    return jsonify({'message': 'Logged out successfully'}), 200

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_price(value):
    """Parse price from various formats to float"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    cleaned = re.sub(r'[^\d.]', '', str(value))
    return float(cleaned) if cleaned else 0.0

def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    return datetime.now().strftime('%Y-%m-%d')

def is_data_fresh(data_entry):
    """Check if cached data is from today"""
    if not data_entry or 'date' not in data_entry:
        return False
    return data_entry['date'] == get_today_date()

# ============================================================================
# DATABASE-BASED CACHING FUNCTIONS (UPDATED WITH USER SUPPORT)
# ============================================================================

def get_cached_ratios_by_ticker(ticker, user_id):
    """Get cached ratios for a ticker if from today"""
    # Find holding by ticker first
    existing_holding = find_existing_holding_by_ticker(ticker, user_id)
    if not existing_holding:
        return None
    
    # Get cached ratios for this holding
    cached_ratios = get_ratios_cache(existing_holding['id'])
    if cached_ratios and is_data_fresh(cached_ratios):
        print(f"💾 [CACHE] Using cached ratios for {ticker} from {cached_ratios['date']}")
        return cached_ratios['data']
    
    return None

def save_ratios_to_cache_by_ticker(ticker, ratios_data, user_id):
    """Save ratios data to database with today's date"""
    existing_holding = find_existing_holding_by_ticker(ticker, user_id)
    if not existing_holding:
        print(f"⚠️  [CACHE] No holding found for {ticker} to save ratios")
        return
    
    today = get_today_date()
    updated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_ratios_cache(existing_holding['id'], ratios_data, today, updated_time, user_id)
    print(f"💾 [CACHE] Saved ratios for {ticker} with date {today}")

def get_cached_quarterly_by_ticker(ticker, user_id):
    """Get cached quarterly data for a ticker if from today"""
    existing_holding = find_existing_holding_by_ticker(ticker, user_id)
    if not existing_holding:
        return None
    
    cached_quarterly = get_quarterly_cache(existing_holding['id'])
    if cached_quarterly and is_data_fresh(cached_quarterly):
        print(f"💾 [CACHE] Using cached quarterly data for {ticker} from {cached_quarterly['date']}")
        return cached_quarterly['data']
    
    return None

def save_quarterly_to_cache_by_ticker(ticker, quarterly_data, user_id):
    """Save quarterly data to database with today's date"""
    existing_holding = find_existing_holding_by_ticker(ticker, user_id)
    if not existing_holding:
        print(f"⚠️  [CACHE] No holding found for {ticker} to save quarterly data")
        return
    
    today = get_today_date()
    updated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_quarterly_cache(existing_holding['id'], quarterly_data, today, updated_time, user_id)
    print(f"💾 [CACHE] Saved quarterly data for {ticker} with date {today}")

# ============================================================================
# EXTERNAL DATA PROVIDERS
# ============================================================================

def get_company_name_from_screener(ticker):
    """Extract company name from Screener.in using ticker"""
    url = f"https://www.screener.in/company/{ticker}/consolidated/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, url

        soup = BeautifulSoup(response.text, 'html.parser')
        
        div = soup.find('div', {'class': 'flex-row flex-wrap flex-align-center flex-grow'})
        if div:
            h1 = div.find('h1', {'class': 'margin-0 show-from-tablet-landscape'})
            if h1:
                return h1.text.strip(), url
        
        return None, url
        
    except Exception as e:
        print(f"Error fetching from screener: {e}")
        return None, url

def get_kotak_price_from_url(kotak_url):
    """Get current price, previous close, and price change from Kotak URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(kotak_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_container = soup.find('div', {'class': re.compile('TitleGridAndImage_title-grid-and-image-price.*')})
        
        current_price = None
        price_change_full = None
        
        if price_container:
            price_div = price_container.find('div', {'class': re.compile('TitleGridAndImage_title-grid-and-image-price-text.*kotak-heading-2')})
            if price_div:
                current_price = price_div.text.strip()
            
            change_div = price_container.find('div', {'class': re.compile('kotak-text-regular.*TitleGridAndImage_title-grid-and-image-price-subtext.*')})
            if change_div:
                price_change_full = change_div.text.strip()
        
        # Extract previous close
        previous_close = None
        table_rows = soup.find_all('tr', {'class': re.compile('StockDetail_stock-detail-performance-table-data-row.*')})
        
        for row in table_rows:
            label_cell = row.find('td', {'class': re.compile('StockDetail_stock-detail-performance-table-label.*')})
            if label_cell and 'Prev. Close' in label_cell.text:
                value_cell = row.find('td', {'class': re.compile('StockDetail_stock-detail-performance-table-value.*')})
                if value_cell:
                    # Clean the previous close value to extract just the number
                    prev_close_text = value_cell.text.strip()
                    prev_close_cleaned = re.sub(r'[^\d.]', '', prev_close_text)
                    previous_close = prev_close_cleaned if prev_close_cleaned else "0"
                break

        # Parse price change components
        price_change_amount = None
        price_change_percent = None
        
        if price_change_full:
            amount_match = re.search(r'^([+-]?[\d.]+)', price_change_full.strip())
            if amount_match:
                price_change_amount = amount_match.group(1)
            
            percent_match = re.search(r'\(([+-]?[\d.]+%)\)', price_change_full)
            if percent_match:
                price_change_percent = percent_match.group(1)
        
        return {
            'price': current_price,
            'previous_close': previous_close,
            'price_change_amount': price_change_amount,
            'price_change_percent': price_change_percent
        }
            
    except Exception as e:
        print(f"Error fetching Kotak data: {e}")
        return None

def find_working_kotak_url(company_name):
    """Try multiple variations of company name to find the correct Kotak URL"""
    
    def create_base_url_variations(name):
        variations = []
        clean_name = name.strip()
        
        def format_for_url(text):
            text = text.lower()
            text = re.sub(r'\(([^)]*)\)', r'\1', text)
            text = re.sub(r'[^\w\s-]', '', text)
            text = text.replace(' ', '-')
            text = re.sub(r'-+', '-', text)
            return text.strip('-')
        
        var1 = format_for_url(clean_name)
        variations.append(var1)
        
        var2 = re.sub(r'\([^)]*\)', '', clean_name).strip()
        var2 = re.sub(r'\s+', ' ', var2)
        var2 = format_for_url(var2)
        if var2 != var1:
            variations.append(var2)
        
        var3 = clean_name
        if var3.endswith(' Ltd'):
            var3 = var3[:-4]
        elif var3.endswith(' Limited'):
            var3 = var3[:-8]
        var3 = format_for_url(var3)
        if var3 != var1 and var3 != var2:
            variations.append(var3)
        
        var4 = clean_name
        if var4.endswith(' Ltd'):
            var4 = var4[:-4]
        elif var4.endswith(' Limited'):
            var4 = var4[:-8]
        var4 = re.sub(r'\([^)]*\)', '', var4).strip()
        var4 = re.sub(r'\s+', ' ', var4)
        var4 = format_for_url(var4)
        if var4 not in [var1, var2, var3]:
            variations.append(var4)
        
        return variations
    
    base_variations = create_base_url_variations(company_name)
    all_variations = base_variations + [f"bse-{var}" for var in base_variations]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for i, company_name_url in enumerate(all_variations, 1):
        url = f"https://www.kotaksecurities.com/stocks/{company_name_url}/"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                price_div = soup.find('div', {'class': re.compile('TitleGridAndImage_title-grid-and-image-price-text.*kotak-heading-2')})
                if price_div:
                    price = price_div.text.strip()
                    print(f"✅ Found Kotak price: {price} at {url}")
                    return price, url
                    
        except Exception:
            continue
    
    print(f"❌ All Kotak URL attempts failed for {company_name}")
    return None, None

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/test')
def test_route():
    """Health check endpoint"""
    # Get company count from database
    companies = get_companies_for_suggestions('')
    return jsonify({
        "message": "Flask is working with SQLite!",
        "timestamp": time.time(),
        "database_stats": {
            "companies": len(companies),
            "database": "SQLite portfolio.db"
        }
    })

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get stock search suggestions from database"""
    query = request.args.get('q', '').strip().lower()
    
    if not query or len(query) < 1:
        return jsonify({'suggestions': []})
    
    suggestions = get_companies_for_suggestions(query)
    return jsonify({'suggestions': suggestions[:10]})

@app.route('/api/stock-price')
def get_stock_price():
    """Get stock price with optional detailed ratios"""
    company = request.args.get('company', '').strip()
    detailed = request.args.get('detailed', 'false').lower() == 'true'
    
    if not company:
        return jsonify({"error": "Company name is required"}), 400

    ticker = company.upper().replace(" ", "")

    try:
        # Try to find company in database
        company_data = find_company_by_ticker(ticker)
        response_data = {}
        
        if company_data:
            kotak_data = get_kotak_price_from_url(company_data['kotak_url'])
            if kotak_data and kotak_data['price']:
                response_data = {
                    "name": company_data['name'],
                    "price": kotak_data['price'],
                    "previous_close": kotak_data['previous_close'] or "0",
                    "price_change_amount": kotak_data['price_change_amount'] or "0",
                    "price_change_percent": kotak_data['price_change_percent'] or "0%"
                }
        else:
            # Handle new tickers
            company_name, screener_url = get_company_name_from_screener(ticker)
            
            if not company_name:
                return jsonify({"error": "Company not found"}), 404

            # Check if company exists but with different ticker
            existing_company = find_company_by_ticker(company_name.replace(' ', '').upper())
            
            if existing_company:
                # Update existing company with new ticker
                tickers = existing_company['tickers'] + [ticker]
                screener_urls = existing_company['screener_urls']
                screener_urls[ticker] = screener_url
                
                company_id = get_or_create_company(
                    company_name, tickers, screener_urls, existing_company['kotak_url']
                )
                
                kotak_data = get_kotak_price_from_url(existing_company['kotak_url'])
                if kotak_data and kotak_data['price']:
                    response_data = {
                        "name": company_name,
                        "price": kotak_data['price'],
                        "previous_close": kotak_data['previous_close'] or "0",
                        "price_change_amount": kotak_data['price_change_amount'] or "0",
                        "price_change_percent": kotak_data['price_change_percent'] or "0%"
                    }
            else:
                # Create completely new company
                kotak_price, kotak_url = find_working_kotak_url(company_name)
                if not kotak_price or not kotak_url:
                    return jsonify({"error": "Price not found"}), 404
                
                company_id = get_or_create_company(
                    company_name, [ticker], {ticker: screener_url}, kotak_url
                )
                
                response_data = {
                    "name": company_name,
                    "price": f"₹{kotak_price}",
                    "previous_close": "0"
                }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in get_stock_price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock-ratios/<ticker>')
@jwt_required
def get_stock_ratios(ticker):
    """Get financial ratios - cached if same day, fresh if different day"""
    ticker = ticker.upper()
    print(f"🎯 Ratios requested for {ticker}")
    
    try:
        current_user = get_current_user()
        user_id = current_user['user_id']
        
        # Try to get cached ratios first
        cached_ratios = get_cached_ratios_by_ticker(ticker, user_id)
        if cached_ratios:
            return jsonify({
                'ticker': ticker,
                'ratios': cached_ratios,
                'count': len(cached_ratios),
                'cached': True,
                'source': 'database_cache'
            })
        
        # Scrape fresh ratios
        print(f"🔄 [SCRAPER] Scraping fresh ratios for {ticker}")
        fresh_ratios = scrape_screener_ratios(ticker)
        
        if fresh_ratios:
            save_ratios_to_cache_by_ticker(ticker, fresh_ratios, user_id)
            return jsonify({
                'ticker': ticker,
                'ratios': fresh_ratios,
                'count': len(fresh_ratios),
                'cached': False,
                'source': 'fresh_scrape'
            })
        else:
            return jsonify({"error": "Could not fetch ratios"}), 404
            
    except Exception as e:
        print(f"Error fetching ratios for {ticker}: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/quarterly-results/<ticker>')
@jwt_required
def get_quarterly_results(ticker):
    """Get quarterly results - cached if same day, fresh if different day"""
    ticker = ticker.upper()
    print(f"📊 Quarterly results requested for {ticker}")
    
    try:
        current_user = get_current_user()
        user_id = current_user['user_id']
        
        # Try to get cached quarterly data first
        cached_quarterly = get_cached_quarterly_by_ticker(ticker, user_id)
        if cached_quarterly:
            return jsonify({
                'quarterly_data': cached_quarterly,
                'cached': True,
                'source': 'database_cache'
            })
        
        # Scrape fresh quarterly data
        print(f"🔄 [SCRAPER] Scraping fresh quarterly data for {ticker}")
        fresh_quarterly = scrape_quarterly_results(ticker)
        
        if fresh_quarterly:
            save_quarterly_to_cache_by_ticker(ticker, fresh_quarterly, user_id)
            return jsonify({
                'quarterly_data': fresh_quarterly,
                'cached': False,
                'source': 'fresh_scrape'
            })
        else:
            return jsonify({'error': 'No quarterly data found'}), 404
            
    except Exception as e:
        print(f"❌ [API] Error in quarterly results endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/holdings', methods=['GET'])
@jwt_required
def get_holdings():
    """Get all holdings with updated market prices"""
    try:
        current_user = get_current_user()
        user_id = current_user['user_id']
        
        holdings = get_all_holdings(user_id)
        
        # Update market data for all holdings
        for holding in holdings:
            # Find company data for price updates
            company_data = find_company_by_ticker(holding['ticker'])
            if company_data:
                kotak_data = get_kotak_price_from_url(company_data['kotak_url'])
                if kotak_data:
                    price_updates = {}
                    if kotak_data['price']:
                        price_updates['marketPrice'] = f"₹{kotak_data['price']}"
                        holding['marketPrice'] = f"₹{kotak_data['price']}"
                    if kotak_data['previous_close']:
                        price_updates['previousClose'] = kotak_data['previous_close']
                        holding['previousClose'] = kotak_data['previous_close']
                    if kotak_data['price_change_amount']:
                        price_updates['priceChangeAmount'] = kotak_data['price_change_amount']
                        holding['priceChangeAmount'] = kotak_data['price_change_amount']
                    if kotak_data['price_change_percent']:
                        price_updates['priceChangePercent'] = kotak_data['price_change_percent']
                        holding['priceChangePercent'] = kotak_data['price_change_percent']
                    
                    # Update database
                    if price_updates:
                        update_holding_prices(holding['id'], price_updates)
        
        return jsonify({"holdings": holdings})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings', methods=['POST'])
@jwt_required
def add_holding():
    """Add a new holding or update existing one"""
    try:
        current_user = get_current_user()
        user_id = current_user['user_id']
        
        holding_data = request.get_json() or {}
        date = (holding_data.get('date') or '').strip()

        ticker = (holding_data.get('ticker') or holding_data.get('symbol') or "").strip().lower()
        if not ticker:
            return jsonify({"error": "Ticker is required"}), 400

        try:
            new_qty = int(float(holding_data.get('quantity', 0)))
        except Exception:
            return jsonify({"error": "Invalid quantity"}), 400
        if new_qty <= 0:
            return jsonify({"error": "Quantity must be > 0"}), 400

        new_price_num = parse_price(holding_data.get('price') or holding_data.get('buyPrice'))
        if new_price_num <= 0:
            return jsonify({"error": "Buy price must be > 0"}), 400

        # Get company information
        company_name = holding_data.get('name', ticker.upper())
        exchange = holding_data.get('exchange', 'NSE')
        
        # Find or create company
        company_data = find_company_by_ticker(ticker)
        if not company_data:
            # Create new company entry (basic data)
            company_id = get_or_create_company(
                company_name, [ticker.upper()], 
                {ticker.upper(): f"https://www.screener.in/company/{ticker.upper()}/consolidated/"}, 
                ""
            )
        else:
            company_id = company_data['id']

        # Check for existing holding (ADD user_id parameter)
        existing_holding = find_existing_holding_by_ticker(ticker, user_id)
        
        if existing_holding:
            # Update existing holding
            exist_qty = existing_holding['quantity']
            exist_price_num = existing_holding['avgPrice']
            
            total_qty = exist_qty + new_qty
            avg_price = ((exist_price_num * exist_qty) + (new_price_num * new_qty)) / total_qty
            
            # Update holding in database
            update_holding_avg_price_and_quantity(existing_holding['id'], total_qty, avg_price)
            
            # Add purchase record (ADD user_id parameter)
            add_purchase(existing_holding['id'], date, new_qty, new_price_num, user_id)
            
            message = "Existing holding updated"
            result_holding = get_holding_by_id(existing_holding['id'])
        else:
            # Create new holding (ADD user_id to holding_data)
            holding_id = create_holding({
                'user_id': user_id,
                'company_id': company_id,
                'name': company_name,
                'symbol': ticker.upper(),
                'ticker': ticker.lower(),
                'quantity': new_qty,
                'avgPrice': new_price_num,
                'price': f"₹{new_price_num:.2f}",
                'exchange': exchange,
                'date': date
            })
            
            # Add purchase record (ADD user_id parameter)
            add_purchase(holding_id, date, new_qty, new_price_num, user_id)
            
            message = "Holding added successfully"
            result_holding = get_holding_by_id(holding_id)

        return jsonify({"message": message, "holding": result_holding}), 201

    except Exception as e:
        print(f"Error in add_holding: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings/<string:holding_id>', methods=['PATCH'])
@jwt_required
def sell_holding_quantity(holding_id):
    """Sell partial or complete holding"""
    try:
        current_user = get_current_user()
        
        sell_quantity = request.json.get("sellQuantity", 0)
        if sell_quantity <= 0:
            return jsonify({"error": "Sell quantity must be positive"}), 400

        success = sell_holding_shares(holding_id, sell_quantity)
        
        if not success:
            return jsonify({"error": "Holding not found"}), 404

        # Check if holding still exists (partial sell) or was completely sold
        remaining_holding = get_holding_by_id(holding_id)
        
        if remaining_holding:
            message = f"Sold {sell_quantity} shares, {remaining_holding['quantity']} remaining"
        else:
            message = "Holding fully sold and removed"

        return jsonify({"message": message})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# DEBUG ROUTES
# ============================================================================

@app.route('/debug/routes')
def list_routes():
    """List all registered routes"""
    import urllib.parse
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        line = urllib.parse.unquote(f"{rule.endpoint}: {rule.rule} [{methods}]")
        output.append(line)
    return '<br>'.join(output)

@app.route('/debug/test-scraper')
def test_scraper_route():
    """Test scraper functionality"""
    try:
        from scraper import test_scraper
        result = test_scraper('AXISBANK')
        return jsonify({
            "success": bool(result),
            "ratios_found": len(result) if result else 0,
            "sample_ratios": dict(list(result.items())[:3]) if result else {}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting Stock Portfolio App with SQLite...")
    
    # Get database stats
    companies = get_companies_for_suggestions('')
    
    print(f"🗄️ Database stats: {len(companies)} companies")
    
    print("\n📋 Registered Routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        print(f"   {rule.endpoint}: {rule.rule} [{methods}]")
    
    app.run(debug=True, port=5000)
