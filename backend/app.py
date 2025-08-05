from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/api/stock-price')
def get_stock_price():
    company = request.args.get('company', '').strip()
    exchange = request.args.get('exchange', 'NSE').strip()

    if not company:
        return jsonify({"error": "Company name is required"}), 400

    symbol = company.upper().replace(" ", "")

    exchange_code = exchange.upper()
    if exchange_code == "BSE":
        exchange_code = "BOM"  # Use BOM for BSE on Google Finance

    url = f"https://www.google.com/finance/quote/{symbol}:{exchange_code}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.find("div", class_="YMlKec fxKbKc")
        name_element = soup.find("div", class_="zzDege")


        if price_element and name_element:
            return jsonify({
                "name": name_element.text,
                "price": price_element.text
            })
        else:
            return jsonify({"error": "Price or name not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# New endpoint to get holdings
@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    try:
        if os.path.exists('holdings.json'):
            with open('holdings.json', 'r') as file:
                data = json.load(file)
                return jsonify(data)
        else:
            return jsonify({"holdings": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# New endpoint to add holding
@app.route('/api/holdings', methods=['POST'])
def add_holding():
    try:
        # Get data from request
        holding_data = request.get_json()
        
        # Add timestamp
        holding_data['purchaseDate'] = datetime.now().isoformat()
        holding_data['id'] = datetime.now().timestamp()  # Simple ID
        
        # Read existing holdings
        if os.path.exists('holdings.json'):
            with open('holdings.json', 'r') as file:
                data = json.load(file)
        else:
            data = {"holdings": []}
        
        # Add new holding
        data['holdings'].append(holding_data)
        
        # Write back to file
        with open('holdings.json', 'w') as file:
            json.dump(data, file, indent=2)
        
        return jsonify({"message": "Holding added successfully", "holding": holding_data})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/holdings/<float:holding_id>', methods=['DELETE'])
def delete_holding(holding_id):
    try:
        if not os.path.exists('holdings.json'):
            return jsonify({"error": "Holdings file not found"}), 404

        with open('holdings.json', 'r') as file:
            data = json.load(file)

        # Filter out the holding with the given id
        original_length = len(data['holdings'])
        data['holdings'] = [h for h in data['holdings'] if h['id'] != holding_id]

        if len(data['holdings']) == original_length:
            return jsonify({"error": "Holding not found"}), 404

        with open('holdings.json', 'w') as file:
            json.dump(data, file, indent=2)

        return jsonify({"message": "Holding removed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/holdings/<float:holding_id>', methods=['PATCH'])
def sell_holding_quantity(holding_id):
    """
    Reduces the quantity of a holding by the sold amount.
    If quantity reaches zero or less, removes the holding.
    Expects JSON with {"sellQuantity": number}
    """
    try:
        if not os.path.exists('holdings.json'):
            return jsonify({"error": "Holdings file not found"}), 404
        
        with open('holdings.json', 'r') as file:
            data = json.load(file)

        holding_found = False
        update_message = ""

        sell_quantity = request.json.get("sellQuantity", 0)
        if sell_quantity <= 0:
            return jsonify({"error": "Sell quantity must be positive"}), 400

        new_holdings = []
        for holding in data.get('holdings', []):
            if holding['id'] == holding_id:
                holding_found = True
                current_qty = holding.get('quantity', 0)
                if sell_quantity >= current_qty:
                    # Remove entire holding
                    update_message = "Holding fully sold and removed."
                    # do not add to new_holdings to remove it
                else:
                    # Reduce quantity
                    holding['quantity'] = current_qty - sell_quantity
                    update_message = f"Sold {sell_quantity} shares, remaining {holding['quantity']}."
                    new_holdings.append(holding)
            else:
                new_holdings.append(holding)
        
        if not holding_found:
            return jsonify({"error": "Holding not found"}), 404

        data['holdings'] = new_holdings

        # Write updated holdings back to JSON
        with open('holdings.json', 'w') as file:
            json.dump(data, file, indent=2)

        return jsonify({"message": update_message})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)  