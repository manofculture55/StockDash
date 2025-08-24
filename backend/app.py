from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import re

app = Flask(__name__)
CORS(app)

HOLDINGS_FILE = 'holdings.json'
STOCK_CACHE_FILE = 'stock_cache.json'

# -------------------- Stock Cache Functions (from our skeleton) --------------------
def load_stock_cache():
    """Load existing stock cache from JSON file"""
    if os.path.exists(STOCK_CACHE_FILE):
        try:
            with open(STOCK_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_stock_cache(cache):
    """Save stock cache to JSON file"""
    try:
        with open(STOCK_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=4)
        print(f"💾 Stock cache saved to {STOCK_CACHE_FILE}")
    except Exception as e:
        print(f"❌ Error saving stock cache: {e}")

# Load stock cache on startup
stock_cache = load_stock_cache()
print(f"📂 Loaded {len(stock_cache)} cached companies from stock cache")

def find_company_by_ticker(ticker):
    """Find company data by ticker from cache"""
    for company_name, data in stock_cache.items():
        if ticker in data.get('tickers', []):
            return company_name, data
    return None, None

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
        
        # Look for the specific div structure
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
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract current price and 1-day change
            price_container = soup.find('div', {'class': re.compile('TitleGridAndImage_title-grid-and-image-price.*')})
            
            current_price = None
            price_change_full = None
            
            if price_container:
                # Current price
                price_div = price_container.find('div', {'class': re.compile('TitleGridAndImage_title-grid-and-image-price-text.*kotak-heading-2')})
                if price_div:
                    current_price = price_div.text.strip()
                
                # Price change (amount and percentage)
                change_div = price_container.find('div', {'class': re.compile('kotak-text-regular.*TitleGridAndImage_title-grid-and-image-price-subtext.*')})
                if change_div:
                    price_change_full = change_div.text.strip()  # "-9.45 (-1.14%)"
            
            # Extract previous close from performance table
            previous_close = None
            table_rows = soup.find_all('tr', {'class': re.compile('StockDetail_stock-detail-performance-table-data-row.*')})
            
            for row in table_rows:
                label_cell = row.find('td', {'class': re.compile('StockDetail_stock-detail-performance-table-label.*')})
                if label_cell and 'Prev. Close' in label_cell.text:
                    value_cell = row.find('td', {'class': re.compile('StockDetail_stock-detail-performance-table-value.*')})
                    if value_cell:
                        previous_close = value_cell.text.strip()
                    break
            
            # Parse price change amount and percentage
            price_change_amount = None
            price_change_percent = None
            
            if price_change_full:  # "-9.45 (-1.14%)"
                # Extract amount: -9.45
                amount_match = re.search(r'^([+-]?[\d.]+)', price_change_full.strip())
                if amount_match:
                    price_change_amount = amount_match.group(1)
                
                # Extract percentage: -1.14%
                percent_match = re.search(r'\(([+-]?[\d.]+%)\)', price_change_full)
                if percent_match:
                    price_change_percent = percent_match.group(1)
            
            return {
                'price': current_price,
                'previous_close': previous_close,
                'price_change_amount': price_change_amount,
                'price_change_percent': price_change_percent
            }
                
        return None
        
    except Exception as e:
        print(f"❌ Error fetching data from cached URL: {e}")
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
    all_variations = []
    all_variations.extend(base_variations)
    bse_variations = [f"bse-{var}" for var in base_variations]
    all_variations.extend(bse_variations)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for i, company_name_url in enumerate(all_variations, 1):
        url = f"https://www.kotaksecurities.com/stocks/{company_name_url}/"
        
        is_bse_attempt = company_name_url.startswith('bse-')
        attempt_type = "BSE" if is_bse_attempt else "Normal"
        
        print(f"Attempt {i} ({attempt_type}): Trying URL - {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                price_div = soup.find('div', {'class': re.compile('TitleGridAndImage_title-grid-and-image-price-text.*kotak-heading-2')})
                if price_div:
                    price = price_div.text.strip()
                    print(f"✅ Success! Found price: {price} at URL: {url} ({attempt_type})")
                    return price, url
                    
        except Exception as e:
            print(f"❌ Attempt {i} ({attempt_type}) failed: {e}")
            continue
    
    print(f"❌ All {len(all_variations)} attempts failed")
    return None, None

def update_cache_with_new_ticker(company_name, ticker, screener_url, kotak_url):
    """Add new ticker to existing company or create new company entry"""
    if company_name in stock_cache:
        # Company exists, add ticker if not already present
        if ticker not in stock_cache[company_name]['tickers']:
            stock_cache[company_name]['tickers'].append(ticker)
            stock_cache[company_name]['screener_urls'][ticker] = screener_url
            print(f"🔗 Added new ticker {ticker} to existing company: {company_name}")
    else:
        # New company
        stock_cache[company_name] = {
            'tickers': [ticker],
            'screener_urls': {ticker: screener_url},
            'kotak_url': kotak_url
        }
        print(f"🆕 Created new company entry: {company_name}")

# -------------------- Original Helper Functions --------------------
def read_holdings():
    if os.path.exists(HOLDINGS_FILE):
        with open(HOLDINGS_FILE, 'r') as file:
            return json.load(file)
    return {"holdings": []}

def write_holdings(data):
    with open(HOLDINGS_FILE, 'w') as file:
        json.dump(data, file, indent=2)

def parse_price(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value)
    s = re.sub(r'[^\d.]', '', s)
    return float(s) if s else 0.0

def migrate_transactions_to_purchases(data):
    """One-time compatibility: turn `transactions` (with qty) into `purchases` (with quantity)."""
    changed = False
    for h in data.get("holdings", []):
        if "transactions" in h and "purchases" not in h:
            purchases = []
            for t in h.get("transactions", []):
                qty = t.get("quantity", t.get("qty", 0))
                try:
                    qty = int(float(qty))
                except Exception:
                    qty = 0
                price_num = parse_price(t.get("price", 0))
                purchases.append({
                    "date": t.get("date"),
                    "quantity": qty,
                    "price": round(price_num, 2)
                })
            h["purchases"] = purchases
            h.pop("transactions", None)
            changed = True
    if changed:
        write_holdings(data)
    return data

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """API endpoint to provide search suggestions (FIXED - no duplicates per company)"""
    query = request.args.get('q', '').strip().lower()
    
    if not query or len(query) < 1:
        return jsonify({'suggestions': []})
    
    suggestions = []
    
    for company_name, data in stock_cache.items():
        # Check if query matches company name or any ticker
        match_company = query in company_name.lower()
        match_ticker = any(query in ticker.lower() for ticker in data['tickers'])
        
        if match_company or match_ticker:
            # Pick primary ticker (shortest one, typically NSE symbol like SBIN)
            primary_ticker = min(data['tickers'], key=len)
            
            # Create display text showing primary + other tickers
            display_ticker = primary_ticker
            if len(data['tickers']) > 1:
                other_tickers = [t for t in data['tickers'] if t != primary_ticker]
                display_ticker += f" ({', '.join(other_tickers)})"
            
            suggestions.append({
                'ticker': primary_ticker,  # This is what gets filled in the input
                'company_name': company_name,
                'display_ticker': display_ticker,  # This is what shows in dropdown
                'all_tickers': data['tickers']
            })
    
    # Limit to top 10 suggestions (each company appears only once)
    suggestions = suggestions[:10]
    
    return jsonify({'suggestions': suggestions})



# -------------------- Updated Stock Price Route (REPLACED GOOGLE FINANCE) --------------------

@app.route('/api/stock-price')
def get_stock_price():
    """
    UPDATED: Returns price, previous close, and price change data
    """
    company = request.args.get('company', '').strip()
    exchange = request.args.get('exchange', 'NSE').strip()

    if not company:
        return jsonify({"error": "Company name is required"}), 400

    ticker = company.upper().replace(" ", "")
    print(f"\n🔍 Processing ticker: {ticker} (from holdings system)")

    try:
        # Check cache and get data
        company_name, cached_data = find_company_by_ticker(ticker)
        
        if company_name and cached_data:
            print(f"🎯 Found {ticker} in cache for company: {company_name}")
            
            # Get comprehensive data from Kotak
            kotak_data = get_kotak_price_from_url(stock_cache[company_name]['kotak_url'])
            if kotak_data and kotak_data['price']:  # ✅ Changed
                return jsonify({
                    "name": company_name,
                    "price": kotak_data['price'],                                    # ✅ Changed
                    "previous_close": kotak_data['previous_close'] or "0",          # ✅ Changed
                    "price_change_amount": kotak_data['price_change_amount'] or "0", # ✅ Changed
                    "price_change_percent": kotak_data['price_change_percent'] or "0%" # ✅ Changed
                })

        # STEP 2: Ticker not in cache - do full scraping process
        print(f"🔍 {ticker} not in cache. Starting scraping process...")
        
        # Get company name from Screener.in
        company_name, screener_url = get_company_name_from_screener(ticker)
        
        if not company_name:
            print(f"❌ Company not found on Screener for ticker: {ticker}")
            return jsonify({"error": "Company not found"}), 404

        print(f"📋 Company name from Screener: {company_name}")
        
        # STEP 3: Check if this company already exists with a different ticker
        if company_name in stock_cache:
            print(f"🔗 Found existing company '{company_name}' with tickers: {stock_cache[company_name]['tickers']}")
            
            # Add this ticker to existing company
            update_cache_with_new_ticker(company_name, ticker, screener_url, stock_cache[company_name]['kotak_url'])
            save_stock_cache(stock_cache)
            
            # Get live price from existing Kotak URL
            kotak_data = get_kotak_price_from_url(kotak_url)
            
            if kotak_data and kotak_data['price']:  # ✅ Changed
                return jsonify({
                    "name": company_name,
                    "price": kotak_data['price'],                                    # ✅ Changed
                    "previous_close": kotak_data['previous_close'] or "0",          # ✅ Changed
                    "price_change_amount": kotak_data['price_change_amount'] or "0", # ✅ Changed
                    "price_change_percent": kotak_data['price_change_percent'] or "0%" # ✅ Changed
                })

        # STEP 4: Completely new company - find working Kotak URL
        kotak_price, kotak_url = find_working_kotak_url(company_name)
        
        if not kotak_price or not kotak_url:
            print(f"❌ No working Kotak URL found for: {company_name}")
            return jsonify({"error": "Price not found"}), 404

        # STEP 5: Save new company to cache
        update_cache_with_new_ticker(company_name, ticker, screener_url, kotak_url)
        save_stock_cache(stock_cache)

        # Return formatted response
        return jsonify({
            "name": company_name,
            "price": f"₹{kotak_price}",
            "previous_close": "0"  # Set to 0 for now
        })

    except Exception as e:
        print(f"❌ Error in get_stock_price: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------- Original Routes (UNCHANGED) --------------------

# Get all holdings
@app.route('/api/holdings', methods=['GET'])
def get_holdings():
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
                        # Update holdings.json format
                        if kotak_data['price']:
                            holding['marketPrice'] = f"₹{kotak_data['price']}"
                        
                        if kotak_data['previous_close']:
                            holding['previousClose'] = kotak_data['previous_close']  # Store as number string
                        
                        # Store price change data (new fields)
                        if kotak_data['price_change_amount']:
                            holding['priceChangeAmount'] = kotak_data['price_change_amount']
                        
                        if kotak_data['price_change_percent']:
                            holding['priceChangePercent'] = kotak_data['price_change_percent']
                        
                        # Update company name if missing
                        if not holding.get('name'):
                            holding['name'] = company_name
        
        # Save updated data
        write_holdings(data)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings', methods=['POST'])
def add_holding():
    try:
        holding_data = request.get_json() or {}
        date = (holding_data.get('date') or '').strip()

        # Accept either 'ticker' or fallback to 'symbol'
        ticker = (holding_data.get('ticker') or holding_data.get('symbol') or "").strip().lower()
        if not ticker:
            return jsonify({"error": "Ticker (or symbol) is required"}), 400

        # Parse quantity safely
        try:
            new_qty = int(float(holding_data.get('quantity', 0)))
        except Exception:
            return jsonify({"error": "Invalid quantity"}), 400
        if new_qty <= 0:
            return jsonify({"error": "Quantity must be > 0"}), 400

        # Parse buy price (accepts 'price' or 'buyPrice')
        new_price_num = parse_price(holding_data.get('price') or holding_data.get('buyPrice'))
        if new_price_num <= 0:
            return jsonify({"error": "Buy price must be > 0"}), 400

        # Add unique id (for new entries)
        holding_data['id'] = os.urandom(8).hex()
        holding_data['ticker'] = ticker
        holding_data['date'] = date  # top-level date (optional, legacy)

        # Load existing holdings safely
        if not os.path.exists(HOLDINGS_FILE) or os.stat(HOLDINGS_FILE).st_size == 0:
            data = {"holdings": []}
        else:
            try:
                with open(HOLDINGS_FILE, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {"holdings": []}

        # Find existing holding by ticker (case-insensitive)
        existing_holding = None
        for h in data.get('holdings', []):
            h_ticker = (h.get('ticker') or h.get('symbol') or "").strip().lower()
            if h_ticker == ticker:
                existing_holding = h
                break

        if existing_holding:
            # Parse existing stored price and quantity
            try:
                exist_qty = int(float(existing_holding.get('quantity', 0)))
            except Exception:
                exist_qty = 0
            exist_price_num = parse_price(existing_holding.get('avgPrice') or existing_holding.get('price'))

            total_qty = exist_qty + new_qty

            # Weighted average calculation
            avg_price = 0.0
            if total_qty > 0:
                avg_price = ((exist_price_num * exist_qty) + (new_price_num * new_qty)) / total_qty

            # Update existing holding
            existing_holding['quantity'] = total_qty
            existing_holding['avgPrice'] = round(avg_price, 2)
            existing_holding['price'] = f"₹{avg_price:.2f}"

            # Ensure purchases list exists (and migrate if old key present)
            if 'purchases' not in existing_holding:
                if 'transactions' in existing_holding:
                    # migrate old structure
                    existing_holding['purchases'] = [
                        {"date": t.get("date"),
                         "quantity": int(float(t.get("qty", t.get("quantity", 0)))),
                         "price": round(parse_price(t.get("price", 0)), 2)}
                        for t in existing_holding.get("transactions", [])
                    ]
                    existing_holding.pop("transactions", None)
                else:
                    existing_holding['purchases'] = []

            # Append new purchase
            existing_holding['purchases'].append({
                "qty": None,  # kept for safety but not used
                "date": date,
                "quantity": new_qty,
                "price": round(new_price_num, 2)
            })
            message = "Existing holding updated (quantity and average price recalculated)."
            result_holding = existing_holding

        else:
            # Prepare new holding entry
            holding_data['price'] = f"₹{new_price_num:.2f}"
            holding_data['avgPrice'] = round(new_price_num, 2)
            holding_data['quantity'] = new_qty
            holding_data['purchases'] = [{
                "date": date,
                "quantity": new_qty,
                "price": round(new_price_num, 2)
            }]

            data['holdings'].append(holding_data)
            message = "Holding added successfully."
            result_holding = holding_data

        # Save file
        with open(HOLDINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({"message": message, "holding": result_holding}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Sell part/all of a holding
@app.route('/api/holdings/<string:holding_id>', methods=['PATCH'])
def sell_holding_quantity(holding_id):
    try:
        sell_quantity = request.json.get("sellQuantity", 0)
        if sell_quantity <= 0:
            return jsonify({"error": "Sell quantity must be positive"}), 400

        data = read_holdings()
        holding_found = False
        updated_holdings = []
        message = ""

        for holding in data.get('holdings', []):
            if str(holding['id']) == holding_id:
                holding_found = True
                current_qty = holding.get('quantity', 0)

                if sell_quantity >= current_qty:
                    message = "Holding fully sold and removed."
                else:
                    holding['quantity'] = current_qty - sell_quantity
                    message = f"Sold {sell_quantity} shares, remaining {holding['quantity']}."
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

# -------------------- Main --------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
