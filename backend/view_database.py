import sqlite3

def view_database():
    """View all database tables in a nice tabular format"""
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    print("🗄️ PORTFOLIO DATABASE OVERVIEW")
    print("=" * 50)
    
    # Companies Table
    print("\n📊 COMPANIES TABLE:")
    cursor.execute('SELECT id, name, tickers FROM companies')
    companies = cursor.fetchall()
    print("ID | Company Name | Tickers")
    print("-" * 50)
    for row in companies:
        print(f"{row[0]:2} | {row[1]:<25} | {row[2]}")
    
    # Holdings Table  
    print("\n📈 HOLDINGS TABLE:")
    cursor.execute('SELECT name, symbol, quantity, avgPrice, marketPrice FROM holdings')
    holdings = cursor.fetchall()
    print("Company | Symbol | Qty | Avg Price | Market Price")
    print("-" * 55)
    for row in holdings:
        print(f"{row[0]:<15} | {row[1]:6} | {row[2]:3} | ₹{row[3]:7.2f} | {row[4]}")
    
    # Purchases Table
    print("\n💰 PURCHASES TABLE:")
    cursor.execute('SELECT p.date, h.symbol, p.quantity, p.price FROM purchases p JOIN holdings h ON p.holding_id = h.id')
    purchases = cursor.fetchall()
    print("Date | Symbol | Quantity | Price")
    print("-" * 35)
    for row in purchases:
        print(f"{row[0]} | {row[1]:6} | {row[2]:8} | ₹{row[3]:.2f}")
    
    # Cache Status
    print("\n📊 CACHE STATUS:")
    cursor.execute('SELECT COUNT(*) FROM ratios_cache')
    ratios_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM quarterly_cache')
    quarterly_count = cursor.fetchone()[0]
    print(f"Ratios Cache: {ratios_count} entries")
    print(f"Quarterly Cache: {quarterly_count} entries")
    
    conn.close()
    print("\n✅ Database overview complete!")

if __name__ == "__main__":
    view_database()
