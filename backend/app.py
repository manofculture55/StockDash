from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/api/stock-price')
def get_stock_price():
    company = request.args.get('company', '').strip()
    exchange = request.args.get('exchange', 'NSE').strip()

    if not company:
        return jsonify({"error": "Company name is required"}), 400

    symbol = company.upper().replace(" ", "")
    url = f"https://www.google.com/finance/quote/{symbol}:{exchange.upper()}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        price_element = soup.find("div", class_="YMlKec fxKbKc")

        if price_element:
            return jsonify({"price": price_element.text})
        else:
            return jsonify({"error": "Price not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
