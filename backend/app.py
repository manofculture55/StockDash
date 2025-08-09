from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

HOLDINGS_FILE = 'holdings.json'

# -------------------- Helper Functions --------------------
def read_holdings():
    if os.path.exists(HOLDINGS_FILE):
        with open(HOLDINGS_FILE, 'r') as file:
            return json.load(file)
    return {"holdings": []}

def write_holdings(data):
    with open(HOLDINGS_FILE, 'w') as file:
        json.dump(data, file, indent=2)

# -------------------- Routes --------------------

# Fetch stock price from Google Finance
@app.route('/api/stock-price')
def get_stock_price():
    company = request.args.get('company', '').strip()
    exchange = request.args.get('exchange', 'NSE').strip()

    if not company:
        return jsonify({"error": "Company name is required"}), 400

    symbol = company.upper().replace(" ", "")
    exchange_code = "BOM" if exchange.upper() == "BSE" else exchange.upper()

    url = f"https://www.google.com/finance/quote/{symbol}:{exchange_code}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.find("div", class_="YMlKec fxKbKc")
        name_element = soup.find("div", class_="zzDege")

        if price_element and name_element:
            return jsonify({"name": name_element.text, "price": price_element.text})
        return jsonify({"error": "Price or name not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get all holdings
@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    try:
        return jsonify(read_holdings())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/holdings', methods=['POST'])
def add_holding():
    try:
        holding_data = request.get_json() or {}

        # Accept either 'ticker' or fallback to 'symbol'
        ticker = (holding_data.get('ticker') or holding_data.get('symbol') or "").strip().lower()
        if not ticker:
            return jsonify({"error": "Ticker (or symbol) is required"}), 400

        # Helper to parse price strings like "₹1,000.00" or numbers
        def parse_price(value):
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            s = str(value)
            s = re.sub(r'[^\d.]', '', s)   # remove anything not digit or dot
            return float(s) if s else 0.0

        # Parse quantity safely
        try:
            new_qty = int(float(holding_data.get('quantity', 0)))
        except Exception:
            return jsonify({"error": "Invalid quantity"}), 400
        if new_qty <= 0:
            return jsonify({"error": "Quantity must be > 0"}), 400

        # Parse buy price from incoming payload (accepts 'price' or 'buyPrice')
        new_price_num = parse_price(holding_data.get('price') or holding_data.get('buyPrice'))
        if new_price_num <= 0:
            return jsonify({"error": "Buy price must be > 0"}), 400

        # Add timestamp and id (for new entries)
        holding_data['purchaseDate'] = datetime.now().isoformat()
        holding_data['id'] = datetime.now().timestamp()
        # ensure ticker is saved
        holding_data['ticker'] = ticker

        # Load existing holdings safely (create empty if missing/invalid)
        if not os.path.exists('holdings.json') or os.stat('holdings.json').st_size == 0:
            data = {"holdings": []}
        else:
            try:
                with open('holdings.json', 'r') as f:
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
            existing_holding['avgPrice'] = round(avg_price, 2)   # numeric for calculations
            existing_holding['price'] = f"₹{avg_price:.2f}"      # display version
            message = "Existing holding updated (quantity and average price recalculated)."
            result_holding = existing_holding

        else:
            # Prepare new holding entry: store formatted price and numeric avgPrice
            holding_data['price'] = f"₹{new_price_num:.2f}"
            holding_data['avgPrice'] = round(new_price_num, 2)
            holding_data['quantity'] = new_qty
            data['holdings'].append(holding_data)
            message = "Holding added successfully."
            result_holding = holding_data

        # Save file
        with open('holdings.json', 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({"message": message, "holding": result_holding}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# Sell part/all of a holding
@app.route('/api/holdings/<float:holding_id>', methods=['PATCH'])
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
            if holding['id'] == holding_id:
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
    app.run(debug=True)
