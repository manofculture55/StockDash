"""
Portfolio Database Manager
SQLite database setup and operations for Stock Portfolio Management System
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Any


# Database configuration
DATABASE_PATH = 'portfolio.db'


def get_db_connection():
    """Create and return database connection with proper settings"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
    return conn


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database with all required tables"""
    print("🗄️ Initializing SQLite database...")
    
    with get_db() as conn:
        cursor = conn.cursor()

        # 0. Users table (ADD THIS FIRST)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        
        # 1. Companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tickers TEXT NOT NULL,  -- JSON array: ["ITC", "ITC.NS"]
                screener_urls TEXT NOT NULL,  -- JSON object: {"ITC": "https://..."}
                kotak_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Holdings table (MODIFIED - add user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id TEXT PRIMARY KEY,  -- Keep same format as JSON: "21d9e43236332ad4"
                user_id INTEGER NOT NULL,  -- NEW: User foreign key
                company_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                ticker TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                avgPrice REAL NOT NULL DEFAULT 0.0,
                price TEXT,  -- "₹405.00" format
                marketPrice TEXT,  -- "₹410.65" format
                previousClose TEXT,  -- "411.55" format
                priceChangeAmount TEXT,  -- "-0.90" format
                priceChangePercent TEXT,  -- "-0.22%" format
                exchange TEXT DEFAULT 'NSE',
                date TEXT NOT NULL,  -- "2025-09-21" format
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
            )
        """)

        
        # 3. Purchases table (MODIFIED - add user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,  -- NEW: User foreign key
                holding_id TEXT NOT NULL,
                date TEXT NOT NULL,  -- "2025-09-21" format
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (holding_id) REFERENCES holdings (id) ON DELETE CASCADE
            )
        """)

        
        # 4. Ratios cache table (MODIFIED - add user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratios_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,  -- NEW: User foreign key
                holding_id TEXT NOT NULL UNIQUE,
                ratios_data TEXT NOT NULL,  -- JSON string of all ratios
                cache_date TEXT NOT NULL,  -- "2025-09-21" format
                updated_time TEXT NOT NULL,  -- "2025-09-21 06:25:39" format
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (holding_id) REFERENCES holdings (id) ON DELETE CASCADE
            )
        """)
        
        # 5. Quarterly cache table (MODIFIED - add user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,  -- NEW: User foreign key
                holding_id TEXT NOT NULL UNIQUE,
                quarterly_data TEXT NOT NULL,  -- JSON string of quarterly data
                cache_date TEXT NOT NULL,  -- "2025-09-21" format
                updated_time TEXT NOT NULL,  -- "2025-09-21 06:26:12" format
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (holding_id) REFERENCES holdings (id) ON DELETE CASCADE
            )
        """)

        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_company ON holdings(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_ticker ON holdings(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_holding ON purchases(holding_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratios_holding ON ratios_cache(holding_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quarterly_holding ON quarterly_cache(holding_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
        
        # User-related indexes (ADD THESE)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_user ON holdings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratios_user ON ratios_cache(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quarterly_user ON quarterly_cache(user_id)")


        print("✅ Database tables created successfully!")
        print("✅ Indexes created for better performance!")


def get_or_create_company(name: str, tickers: List[str], screener_urls: Dict[str, str], kotak_url: str) -> int:
    """Get existing company or create new one, return company_id"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Try to find existing company
        cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            company_id = result['id']
            
            # Update tickers and URLs if new ones are provided
            cursor.execute("""
                UPDATE companies 
                SET tickers = ?, screener_urls = ?, kotak_url = ?
                WHERE id = ?
            """, (
                json.dumps(tickers),
                json.dumps(screener_urls),
                kotak_url,
                company_id
            ))
            
            return company_id
        else:
            # Create new company
            cursor.execute("""
                INSERT INTO companies (name, tickers, screener_urls, kotak_url)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                json.dumps(tickers),
                json.dumps(screener_urls),
                kotak_url
            ))
            
            return cursor.lastrowid


def create_holding(holding_data: Dict[str, Any]) -> str:
    """Create new holding record"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Generate ID if not provided
        holding_id = holding_data.get('id') or os.urandom(8).hex()
        
        cursor.execute("""
            INSERT INTO holdings (
                id, user_id, company_id, name, symbol, ticker, quantity, avgPrice,
                price, marketPrice, previousClose, priceChangeAmount, 
                priceChangePercent, exchange, date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            holding_id,
            holding_data['user_id'],  # NEW: Add user_id
            holding_data['company_id'],
            holding_data['name'],
            holding_data['symbol'],
            holding_data['ticker'],
            holding_data['quantity'],
            holding_data['avgPrice'],
            holding_data.get('price', ''),
            holding_data.get('marketPrice', ''),
            holding_data.get('previousClose', ''),
            holding_data.get('priceChangeAmount', ''),
            holding_data.get('priceChangePercent', ''),
            holding_data.get('exchange', 'NSE'),
            holding_data['date']
        ))
        
        return holding_id



def add_purchase(holding_id: str, date: str, quantity: int, price: float, user_id: int):
    """Add purchase record to holding"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO purchases (user_id, holding_id, date, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, holding_id, date, quantity, price))


def get_all_holdings(user_id: int = None) -> List[Dict[str, Any]]:
    """Get all holdings with their purchase history (optionally for specific user)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get holdings (filter by user if provided)
        if user_id:
            cursor.execute("""
                SELECT h.*, c.name as company_name, c.tickers, c.kotak_url
                FROM holdings h
                JOIN companies c ON h.company_id = c.id
                WHERE h.user_id = ?
                ORDER BY h.created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT h.*, c.name as company_name, c.tickers, c.kotak_url
                FROM holdings h
                JOIN companies c ON h.company_id = c.id
                ORDER BY h.created_at DESC
            """)
        
        holdings = []
        for row in cursor.fetchall():
            holding = dict(row)
            
            # Get purchase history
            cursor.execute("""
                SELECT date, quantity, price FROM purchases 
                WHERE holding_id = ? ORDER BY date
            """, (holding['id'],))
            
            purchases = [dict(p) for p in cursor.fetchall()]
            holding['purchases'] = purchases
            
            holdings.append(holding)
        
        return holdings


def get_holding_by_id(holding_id: str) -> Optional[Dict[str, Any]]:
    """Get specific holding by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT h.*, c.name as company_name, c.tickers, c.kotak_url
            FROM holdings h
            JOIN companies c ON h.company_id = c.id
            WHERE h.id = ?
        """, (holding_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        holding = dict(row)
        
        # Get purchase history
        cursor.execute("""
            SELECT date, quantity, price FROM purchases 
            WHERE holding_id = ? ORDER BY date
        """, (holding_id,))
        
        purchases = [dict(p) for p in cursor.fetchall()]
        holding['purchases'] = purchases
        
        return holding


def update_holding_prices(holding_id: str, price_data: Dict[str, str]):
    """Update holding with current market prices"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE holdings 
            SET marketPrice = ?, previousClose = ?, 
                priceChangeAmount = ?, priceChangePercent = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            price_data.get('marketPrice'),
            price_data.get('previousClose'),
            price_data.get('priceChangeAmount'),
            price_data.get('priceChangePercent'),
            holding_id
        ))


def sell_holding_shares(holding_id: str, sell_quantity: int) -> bool:
    """Sell shares from holding, return True if successful"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get current quantity
        cursor.execute("SELECT quantity FROM holdings WHERE id = ?", (holding_id,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        current_quantity = result['quantity']
        
        if sell_quantity >= current_quantity:
            # Delete entire holding
            cursor.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
        else:
            # Update quantity
            new_quantity = current_quantity - sell_quantity
            cursor.execute("""
                UPDATE holdings 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (new_quantity, holding_id))
        
        return True


def save_ratios_cache(holding_id: str, ratios_data: Dict[str, Any], cache_date: str, updated_time: str, user_id: int):
    """Save or update ratios cache"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ratios_cache 
            (user_id, holding_id, ratios_data, cache_date, updated_time)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            holding_id,
            json.dumps(ratios_data),
            cache_date,
            updated_time
        ))


def get_ratios_cache(holding_id: str) -> Optional[Dict[str, Any]]:
    """Get cached ratios for holding"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ratios_data, cache_date, updated_time 
            FROM ratios_cache 
            WHERE holding_id = ?
        """, (holding_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        return {
            'data': json.loads(result['ratios_data']),
            'date': result['cache_date'],
            'updated_time': result['updated_time']
        }


def save_quarterly_cache(holding_id: str, quarterly_data: Dict[str, Any], cache_date: str, updated_time: str, user_id: int):
    """Save or update quarterly cache"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO quarterly_cache 
            (user_id, holding_id, quarterly_data, cache_date, updated_time)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            holding_id,
            json.dumps(quarterly_data),
            cache_date,
            updated_time
        ))


def get_quarterly_cache(holding_id: str) -> Optional[Dict[str, Any]]:
    """Get cached quarterly data for holding"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT quarterly_data, cache_date, updated_time 
            FROM quarterly_cache 
            WHERE holding_id = ?
        """, (holding_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        return {
            'data': json.loads(result['quarterly_data']),
            'date': result['cache_date'],
            'updated_time': result['updated_time']
        }


def get_companies_for_suggestions(query: str) -> List[Dict[str, Any]]:
    """Get companies matching search query for suggestions"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, tickers FROM companies 
            WHERE name LIKE ? OR tickers LIKE ?
            ORDER BY name
            LIMIT 10
        """, (f'%{query}%', f'%{query}%'))
        
        companies = []
        for row in cursor.fetchall():
            tickers = json.loads(row['tickers'])
            primary_ticker = min(tickers, key=len)
            
            companies.append({
                'ticker': primary_ticker,
                'company_name': row['name'],
                'display_ticker': primary_ticker + (f" ({', '.join([t for t in tickers if t != primary_ticker])})" if len(tickers) > 1 else ""),
                'all_tickers': tickers
            })
        
        return companies


def find_company_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """Find company by any of its tickers"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM companies")
        
        for row in cursor.fetchall():
            tickers = json.loads(row['tickers'])
            if ticker.upper() in [t.upper() for t in tickers]:
                company = dict(row)
                company['tickers'] = tickers
                company['screener_urls'] = json.loads(row['screener_urls'])
                return company
        
        return None


def update_holding_avg_price_and_quantity(holding_id: str, new_quantity: int, new_avg_price: float):
    """Update holding quantity and average price (for additional purchases)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE holdings 
            SET quantity = ?, avgPrice = ?, price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_quantity, new_avg_price, f"₹{new_avg_price:.2f}", holding_id))


def find_existing_holding_by_ticker(ticker: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Find existing holding by ticker for specific user"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM holdings 
            WHERE (ticker = ? OR symbol = ?) AND user_id = ?
        """, (ticker.lower(), ticker.upper(), user_id))
        
        result = cursor.fetchone()
        if result:
            return dict(result)
        
        return None

    
# ============================================================================
# USER MANAGEMENT FUNCTIONS
# ============================================================================

def create_user(username: str, email: str, password_hash: str, first_name: str = '', last_name: str = '') -> int:
    """Create new user account"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, first_name, last_name))
        
        return cursor.lastrowid

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        return dict(result) if result else None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        return dict(result) if result else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        return dict(result) if result else None



if __name__ == '__main__':
    # Initialize database when run directly
    init_database()
    print("🎉 Database setup complete! Ready to use SQLite.")
