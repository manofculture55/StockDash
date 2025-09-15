"""
Stock Portfolio Management API
A Flask-based backend for managing stock portfolios with real-time data scraping
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
import traceback

# Import our custom scraper module
from scraper import scrape_screener_ratios

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

app = Flask(__name__)
CORS(app)

# File paths
HOLDINGS_FILE = 'holdings.json'
STOCK_CACHE_FILE = 'stock_cache.json'

# ============================================================================
# CACHE MANAGEMENT FUNCTIONS (STOCK CACHE ONLY)
# ============================================================================

def load_stock_cache():
    """Load existing stock cache from JSON file"""
    if os.path.exists(STOCK_CACHE_FILE):
        try:
            with open(STOCK_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_stock_cache(cache):
    """Save stock cache to JSON file"""
    try:
        with open(STOCK_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        print(f"Error saving stock cache: {e}")

# Initialize stock cache
stock_cache = load_stock_cache()
print(f"📂 Loaded {len(stock_cache)} cached companies")

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

def find_company_by_ticker(ticker):
    """Find company data by ticker from cache"""
    for company_name, data in stock_cache.items():
        if ticker in data.get('tickers', []):
            return company_name, data
    return None, None

# ============================================================================
# DATA PERSISTENCE FUNCTIONS
# ============================================================================

def read_holdings():
    """Load holdings data from file"""
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception:
            pass
    return {"holdings": []}

def write_holdings(data):
    """Save holdings data to file"""
    try:
        with open(HOLDINGS_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
    except Exception as e:
        print(f"Error saving holdings: {e}")

def migrate_transactions_to_purchases(data):
    """Migrate legacy transaction format to purchases format"""
    changed = False
    for holding in data.get("holdings", []):
        if "transactions" in holding and "purchases" not in holding:
            purchases = []
            for transaction in holding.get("transactions", []):
                qty = transaction.get("quantity", transaction.get("qty", 0))
                try:
                    qty = int(float(qty))
                except Exception:
                    qty = 0
                
                price_num = parse_price(transaction.get("price", 0))
                purchases.append({
                    "date": transaction.get("date"),
                    "quantity": qty,
                    "price": round(price_num, 2)
                })
            
            holding["purchases"] = purchases
            holding.pop("transactions", None)
            changed = True
    
    if changed:
        write_holdings(data)
    return data

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
                    previous_close = value_cell.text.strip()
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

def update_cache_with_new_ticker(company_name, ticker, screener_url, kotak_url):
    """Add new ticker to existing company or create new company entry"""
    if company_name in stock_cache:
        if ticker not in stock_cache[company_name]['tickers']:
            stock_cache[company_name]['tickers'].append(ticker)
            stock_cache[company_name]['screener_urls'][ticker] = screener_url
    else:
        stock_cache[company_name] = {
            'tickers': [ticker],
            'screener_urls': {ticker: screener_url},
            'kotak_url': kotak_url
        }

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/test')
def test_route():
    """Health check endpoint"""
    return jsonify({
        "message": "Flask is working!",
        "timestamp": time.time(),
        "cache_stats": {
            "companies": len(stock_cache)
        }
    })

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get stock search suggestions"""
    query = request.args.get('q', '').strip().lower()
    
    if not query or len(query) < 1:
        return jsonify({'suggestions': []})
    
    suggestions = []
    
    for company_name, data in stock_cache.items():
        if (query in company_name.lower() or 
            any(query in ticker.lower() for ticker in data['tickers'])):
            
            primary_ticker = min(data['tickers'], key=len)
            display_ticker = primary_ticker
            
            if len(data['tickers']) > 1:
                other_tickers = [t for t in data['tickers'] if t != primary_ticker]
                display_ticker += f" ({', '.join(other_tickers)})"
            
            suggestions.append({
                'ticker': primary_ticker,
                'company_name': company_name,
                'display_ticker': display_ticker,
                'all_tickers': data['tickers']
            })
    
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
        company_name, cached_data = find_company_by_ticker(ticker)
        response_data = {}
        
        if company_name and cached_data:
            kotak_data = get_kotak_price_from_url(stock_cache[company_name]['kotak_url'])
            if kotak_data and kotak_data['price']:
                response_data = {
                    "name": company_name,
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

            if company_name in stock_cache:
                update_cache_with_new_ticker(company_name, ticker, screener_url, stock_cache[company_name]['kotak_url'])
                save_stock_cache(stock_cache)
                kotak_data = get_kotak_price_from_url(stock_cache[company_name]['kotak_url'])
                if kotak_data and kotak_data['price']:
                    response_data = {
                        "name": company_name,
                        "price": kotak_data['price'],
                        "previous_close": kotak_data['previous_close'] or "0",
                        "price_change_amount": kotak_data['price_change_amount'] or "0",
                        "price_change_percent": kotak_data['price_change_percent'] or "0%"
                    }
            else:
                kotak_price, kotak_url = find_working_kotak_url(company_name)
                if not kotak_price or not kotak_url:
                    return jsonify({"error": "Price not found"}), 404
                
                update_cache_with_new_ticker(company_name, ticker, screener_url, kotak_url)
                save_stock_cache(stock_cache)
                
                response_data = {
                    "name": company_name,
                    "price": f"₹{kotak_price}",
                    "previous_close": "0"
                }

        # Add fresh ratios if requested
        if detailed and response_data:
            print(f"📊 Fresh ratios requested for {ticker}")
            ratios = scrape_screener_ratios(ticker)  # Called from scraper.py
            
            if ratios:
                response_data['ratios'] = ratios
                response_data['ratios_count'] = len(ratios)
            else:
                response_data['ratios'] = {}
                response_data['ratios_count'] = 0

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in get_stock_price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock-ratios/<ticker>')
def get_stock_ratios(ticker):
    """Get fresh detailed financial ratios for a stock"""
    ticker = ticker.upper()
    print(f"🎯 Fresh ratios requested for {ticker}")
    
    try:
        # Always scrape fresh ratios using our separate scraper module
        ratios = scrape_screener_ratios(ticker)  # Called from scraper.py
        
        if ratios:
            return jsonify({
                'ticker': ticker,
                'ratios': ratios,
                'count': len(ratios),
                'cached': False  # Always fresh
            })
        else:
            return jsonify({"error": "Could not fetch ratios"}), 404
            
    except Exception as e:
        print(f"Error fetching ratios for {ticker}: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    """Get all holdings with updated market prices"""
    try:
        data = read_holdings()
        data = migrate_transactions_to_purchases(data)
        
        # Update market data for all holdings
        for holding in data.get('holdings', []):
            ticker = holding.get('ticker') or holding.get('symbol', '')
            if ticker:
                company_name, cached_data = find_company_by_ticker(ticker.upper())
                if company_name and cached_data:
                    kotak_data = get_kotak_price_from_url(cached_data['kotak_url'])
                    if kotak_data:
                        if kotak_data['price']:
                            holding['marketPrice'] = f"₹{kotak_data['price']}"
                        if kotak_data['previous_close']:
                            holding['previousClose'] = kotak_data['previous_close']
                        if kotak_data['price_change_amount']:
                            holding['priceChangeAmount'] = kotak_data['price_change_amount']
                        if kotak_data['price_change_percent']:
                            holding['priceChangePercent'] = kotak_data['price_change_percent']
                        if not holding.get('name'):
                            holding['name'] = company_name
        
        write_holdings(data)
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings', methods=['POST'])
def add_holding():
    """Add a new holding or update existing one"""
    try:
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

        holding_data['id'] = os.urandom(8).hex()
        holding_data['ticker'] = ticker
        holding_data['date'] = date

        # Load existing data
        if not os.path.exists(HOLDINGS_FILE) or os.stat(HOLDINGS_FILE).st_size == 0:
            data = {"holdings": []}
        else:
            try:
                with open(HOLDINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {"holdings": []}

        # Find existing holding
        existing_holding = None
        for h in data.get('holdings', []):
            h_ticker = (h.get('ticker') or h.get('symbol') or "").strip().lower()
            if h_ticker == ticker:
                existing_holding = h
                break

        if existing_holding:
            # Update existing holding
            try:
                exist_qty = int(float(existing_holding.get('quantity', 0)))
            except Exception:
                exist_qty = 0
            exist_price_num = parse_price(existing_holding.get('avgPrice') or existing_holding.get('price'))

            total_qty = exist_qty + new_qty
            
            if total_qty > 0:
                avg_price = ((exist_price_num * exist_qty) + (new_price_num * new_qty)) / total_qty
            else:
                avg_price = new_price_num

            existing_holding['quantity'] = total_qty
            existing_holding['avgPrice'] = round(avg_price, 2)
            existing_holding['price'] = f"₹{avg_price:.2f}"

            # Handle purchase history
            if 'purchases' not in existing_holding:
                if 'transactions' in existing_holding:
                    existing_holding['purchases'] = [
                        {"date": t.get("date"),
                         "quantity": int(float(t.get("qty", t.get("quantity", 0)))),
                         "price": round(parse_price(t.get("price", 0)), 2)}
                        for t in existing_holding.get("transactions", [])
                    ]
                    existing_holding.pop("transactions", None)
                else:
                    existing_holding['purchases'] = []

            existing_holding['purchases'].append({
                "date": date,
                "quantity": new_qty,
                "price": round(new_price_num, 2)
            })
            
            message = "Existing holding updated"
            result_holding = existing_holding
        else:
            # Create new holding
            holding_data['price'] = f"₹{new_price_num:.2f}"
            holding_data['avgPrice'] = round(new_price_num, 2)
            holding_data['quantity'] = new_qty
            holding_data['purchases'] = [{
                "date": date,
                "quantity": new_qty,
                "price": round(new_price_num, 2)
            }]

            data['holdings'].append(holding_data)
            message = "Holding added successfully"
            result_holding = holding_data

        # Save data
        with open(HOLDINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return jsonify({"message": message, "holding": result_holding}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings/<string:holding_id>', methods=['PATCH'])
def sell_holding_quantity(holding_id):
    """Sell partial or complete holding"""
    try:
        sell_quantity = request.json.get("sellQuantity", 0)
        if sell_quantity <= 0:
            return jsonify({"error": "Sell quantity must be positive"}), 400

        data = read_holdings()
        holding_found = False
        updated_holdings = []

        for holding in data.get('holdings', []):
            if str(holding['id']) == holding_id:
                holding_found = True
                current_qty = holding.get('quantity', 0)

                if sell_quantity >= current_qty:
                    message = "Holding fully sold and removed"
                else:
                    holding['quantity'] = current_qty - sell_quantity
                    message = f"Sold {sell_quantity} shares, {holding['quantity']} remaining"
                    updated_holdings.append(holding)
            else:
                updated_holdings.append(holding)

        if not holding_found:
            return jsonify({"error": "Holding not found"}), 404

        data['holdings'] = updated_holdings
        write_holdings(data)
        return jsonify({"message": message})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# DEBUG ROUTES (Remove in production)
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
    print("🚀 Starting Stock Portfolio App...")
    print(f"📂 Stock cache: {len(stock_cache)} entries")
    
    print("\n📋 Registered Routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        print(f"   {rule.endpoint}: {rule.rule} [{methods}]")
    
    app.run(debug=True, port=5000)
