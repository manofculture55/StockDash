/**
 * Stock Market Dashboard - Main App Component
 * Provides stock search, price fetching, and portfolio management functionality
 */

import React, { useState, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Holdings from "./pages/Holdings";
import HoldingDetails from "./pages/HoldingDetails";
import "./App.css";
import { ThemeProvider, ThemeToggle } from './ThemeContext';

// Configuration and utilities
const API_BASE_URL = "http://localhost:5000/api";

const detectExchange = (ticker) => {
  return /^\d+$/.test(ticker.trim()) ? "BSE" : "NSE";
};

function App() {
  // State management
  const [company, setCompany] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");
  const [companyFullName, setCompanyFullName] = useState("");
  const [previousClose, setPreviousClose] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Modal state
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [buyQuantity, setBuyQuantity] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  
  // Refs for managing timeouts
  const suggestionsTimeoutRef = useRef(null);

  // Modal management
  const openBuyModal = () => {
    setShowBuyModal(true);
    const cleanPrice = price.replace(/[^\d.-]/g, "");
    setBuyPrice(cleanPrice);
  };

  const closeBuyModal = () => {
    setShowBuyModal(false);
    setBuyQuantity("");
    setBuyPrice("");
    setPurchaseDate("");
  };

  // API functions
  const fetchSuggestions = async (query) => {
    if (query.length < 1) return [];
    
    try {
      const response = await fetch(`${API_BASE_URL}/suggestions?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      return data.suggestions || [];
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      return [];
    }
  };

  const fetchStockPrice = async () => {
    if (!company.trim()) {
      setError("Please enter a stock symbol");
      return;
    }

    setPrice("");
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/stock-price?company=${encodeURIComponent(company)}`);
      const data = await response.json();
      
      if (data.price) {
        setPrice(data.price);
        setCompanyFullName(data.name || "");
        setPreviousClose(data.previous_close || "");
        setError("");
      } else {
        setError(data.error || "Price not found");
      }
    } catch (error) {
      setError("Failed to fetch stock price");
    }
  };

  // Input handlers
  const handleCompanyInputChange = (e) => {
    const query = e.target.value;
    setCompany(query.toUpperCase());
    
    // Clear existing timeout
    if (suggestionsTimeoutRef.current) {
      clearTimeout(suggestionsTimeoutRef.current);
    }
    
    if (query.length >= 1) {
      suggestionsTimeoutRef.current = setTimeout(async () => {
        const suggestionList = await fetchSuggestions(query);
        setSuggestions(suggestionList);
        setShowSuggestions(true);
      }, 300);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (selectedTicker) => {
    setCompany(selectedTicker.toUpperCase());
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const hideSuggestions = () => {
    setTimeout(() => setShowSuggestions(false), 200);
  };

  const handleInputFocus = () => {
    if (company.length >= 1 && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  // Stock purchase handler
  const handleStockPurchase = async () => {
    // Validation
    const quantity = parseInt(buyQuantity, 10);
    if (!quantity || quantity <= 0) {
      alert("Please enter a valid quantity");
      return;
    }

    const priceValue = parseFloat(buyPrice);
    if (!priceValue || priceValue <= 0) {
      alert("Please enter a valid buying price");
      return;
    }

    if (!purchaseDate.trim()) {
      alert("Please enter a purchase date");
      return;
    }

    const exchange = detectExchange(company);
    
    const holdingData = {
      name: companyFullName || company,
      symbol: company,
      ticker: company,
      price: priceValue,
      marketPrice: price,
      previousClose: previousClose,
      quantity: quantity,
      exchange: exchange,
      date: purchaseDate
    };

    try {
      const response = await fetch(`${API_BASE_URL}/holdings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(holdingData),
      });

      const data = await response.json();
      
      if (data.message) {
        alert("Stock added to holdings successfully!");
        closeBuyModal();
        // Clear form data
        setCompany("");
        setPrice("");
        setCompanyFullName("");
        setPreviousClose("");
      } else {
        alert(data.error || "Error adding stock to holdings");
      }
    } catch (error) {
      alert("Failed to add stock to holdings");
    }
  };

  return (
    <ThemeProvider>
      <Router>
        <div className="app-container">
          {/* Header */}
          <header className="app-header">
            {/* Top row: Title and Theme Toggle */}
            <div className="header-top-row">
              <h1 className="app-title">OneAsset Dashboard</h1>
              <ThemeToggle />
            </div>

            {/* Second row: Navigation buttons */}
            <nav className="navigation">
              <Link to="/" className="nav-link">
                <button className="nav-button">Home</button>
              </Link>
              <Link to="/holdings" className="nav-link">
                <button className="nav-button">Holdings</button>
              </Link>
            </nav>
          </header>

          <main className="main-content">
            <Routes>
              {/* Home Page */}
              <Route
                path="/"
                element={
                  <div className="home-page">
                    <div className="search-section">
                      <div className="search-container">
                        <div className="search-input-wrapper">
                          <svg className="search-icon" viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z" />
                          </svg>
                          
                          <input
                            type="search"
                            placeholder="Enter Stock"
                            className="search-input"
                            value={company}
                            onChange={handleCompanyInputChange}
                            onBlur={hideSuggestions}
                            onFocus={handleInputFocus}
                          />
                          
                          {/* Suggestions Dropdown */}
                          {showSuggestions && suggestions.length > 0 && (
                            <div className="suggestions-dropdown">
                              {suggestions.map((item, index) => (
                                <div
                                  key={index}
                                  className="suggestion-item"
                                  onClick={() => handleSuggestionClick(item.ticker)}
                                >
                                  <div className="suggestion-ticker">
                                    {item.display_ticker || item.ticker}
                                  </div>
                                  <div className="suggestion-company">
                                    {item.company_name}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        <button 
                          className="fetch-button" 
                          onClick={fetchStockPrice}
                          disabled={!company.trim()}
                        >
                          Search
                        </button>
                      </div>
                    </div>

                    {/* Results Section */}
                    {price && (
                      <div className="results-section">
                        <div className="stock-card">
                          <div className="stock-info">
                            <h3 className="company-name">{companyFullName || company}</h3>
                            <p className="stock-price">Current Price: {price}</p>
                            {previousClose && (
                              <p className="previous-close">Previous Close: ₹{previousClose}</p>
                            )}
                          </div>
                          <button className="buy-button" onClick={openBuyModal}>
                            Add to Portfolio
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Error Display */}
                    {error && (
                      <div className="error-section">
                        <p className="error-message">{error}</p>
                      </div>
                    )}
                  </div>
                }
              />

              {/* Holdings Page */}
              <Route path="/holdings" element={<Holdings />} />
              
              {/* Holding Details Page */}
              <Route path="/holding-details/:id" element={<HoldingDetails />} />
            </Routes>
          </main>

          {/* Buy Modal */}
          {showBuyModal && (
            <div className="modal-overlay" onClick={closeBuyModal}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h2 className="modal-title">
                    Add to Portfolio: {companyFullName || company}
                  </h2>
                  <button className="modal-close-button" onClick={closeBuyModal}>
                    ×
                  </button>
                </div>

                <div className="modal-body">
                  <p className="current-price">Current Price: {price}</p>

                  <div className="form-group">
                    <label htmlFor="quantity" className="form-label">
                      Quantity
                    </label>
                    <input
                      id="quantity"
                      type="number"
                      min="1"
                      placeholder="Enter quantity"
                      className="form-input"
                      value={buyQuantity}
                      onChange={(e) => setBuyQuantity(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="buyPrice" className="form-label">
                      Purchase Price (₹)
                    </label>
                    <input
                      id="buyPrice"
                      type="number"
                      step="0.01"
                      min="0.01"
                      placeholder="Enter purchase price"
                      className="form-input"
                      value={buyPrice}
                      onChange={(e) => setBuyPrice(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="purchaseDate" className="form-label">
                      Purchase Date
                    </label>
                    <input
                      id="purchaseDate"
                      type="date"
                      className="form-input"
                      value={purchaseDate}
                      onChange={(e) => setPurchaseDate(e.target.value)}
                    />
                  </div>
                </div>

                <div className="modal-footer">
                  <button className="cancel-button" onClick={closeBuyModal}>
                    Cancel
                  </button>
                  <button className="confirm-button" onClick={handleStockPurchase}>
                    Add to Portfolio
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
