/**
 * Holdings Component
 * Displays portfolio holdings with live price updates, portfolio summary,
 * and sell functionality
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import './Holdings.css';

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';
const MARKET_HOURS = {
  start: { hour: 9, minute: 0 },
  end: { hour: 15, minute: 30 }
};
const LIVE_UPDATE_INTERVAL = 30000; // 30 seconds

function Holdings() {
  // State management
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [liveUpdate, setLiveUpdate] = useState(false);

  // Sell modal state
  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [sellQuantity, setSellQuantity] = useState('');

  const navigate = useNavigate();

  // Utility functions
  const parsePrice = (priceString) => {
    if (!priceString) return 0;
    const cleaned = priceString.toString().replace(/[^\d.-]/g, '');
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? 0 : parsed;
  };

  const isMarketOpen = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    
    return (
      (hours > MARKET_HOURS.start.hour || 
       (hours === MARKET_HOURS.start.hour && minutes >= MARKET_HOURS.start.minute)) &&
      (hours < MARKET_HOURS.end.hour || 
       (hours === MARKET_HOURS.end.hour && minutes <= MARKET_HOURS.end.minute))
    );
  };

  // Data fetching
  useEffect(() => {
    fetchHoldings();

    let interval = null;
    if (liveUpdate) {
      interval = setInterval(() => {
        if (isMarketOpen()) {
          fetchHoldings();
        }
      }, LIVE_UPDATE_INTERVAL);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [liveUpdate]);

  const fetchHoldings = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/holdings`);
      const data = await response.json();
      
      if (response.ok) {
        setHoldings(data.holdings || []);
        setError('');
      } else {
        setError(data.error || 'Failed to fetch holdings');
      }
    } catch (err) {
      setError('Failed to fetch holdings');
    } finally {
      setLoading(false);
    }
  };

  // Modal management
  const openSellModal = (holding) => {
    setSelectedHolding(holding);
    setSellQuantity('');
    setShowSellModal(true);
  };

  const closeSellModal = () => {
    setShowSellModal(false);
    setSelectedHolding(null);
    setSellQuantity('');
  };

  // Sell functionality
  const handleSellStock = async () => {
    const quantity = parseInt(sellQuantity, 10);
    
    if (!quantity || quantity <= 0 || quantity > selectedHolding.quantity) {
      alert(`Please enter a valid quantity (1 - ${selectedHolding.quantity})`);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/holdings/${selectedHolding.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sellQuantity: quantity }),
      });

      const data = await response.json();
      
      if (response.ok) {
        alert(data.message || 'Stock sold successfully');
        fetchHoldings();
        closeSellModal();
      } else {
        alert(data.error || 'Error processing sell request');
      }
    } catch (err) {
      alert('Failed to process sell request');
    }
  };

  // Portfolio calculations
  const portfolioMetrics = useMemo(() => {
    let totalInvested = 0;
    let totalCurrent = 0;
    let totalPrevCloseValue = 0;

    holdings.forEach(holding => {
      const avgPrice = parsePrice(holding.avgPrice);
      const marketPrice = parsePrice(holding.marketPrice);
      const previousClose = parsePrice(holding.previousClose);
      const quantity = parseInt(holding.quantity, 10) || 0;

      totalInvested += avgPrice * quantity;
      totalCurrent += marketPrice * quantity;
      totalPrevCloseValue += previousClose * quantity;
    });

    const totalReturns = totalCurrent - totalInvested;
    const totalReturnsPercent = totalInvested > 0 ? (totalReturns / totalInvested) * 100 : 0;
    const totalOneDayChange = totalCurrent - totalPrevCloseValue;
    const totalOneDayChangePercent = totalPrevCloseValue > 0 ? 
      (totalOneDayChange / totalPrevCloseValue) * 100 : 0;

    return {
      totalInvested,
      totalCurrent,
      totalReturns,
      totalReturnsPercent,
      totalOneDayChange,
      totalOneDayChangePercent
    };
  }, [holdings]);

  // Loading state
  if (loading) {
    return (
      <div className="holdings-loading">
        <div className="loading-spinner">Loading holdings...</div>
      </div>
    );
  }

  return (
    <div className="holdings-container">
      {/* Header */}
      <header className="holdings-header">
        <h2 className="holdings-title">My Portfolio</h2>
        
        <div className="live-update-toggle">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={liveUpdate}
              onChange={() => setLiveUpdate(!liveUpdate)}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">
            Live Updates {liveUpdate && isMarketOpen() && '🟢'}
          </span>
        </div>
      </header>

      {/* Portfolio Summary */}
      <section className="portfolio-summary">
        <div className="summary-header">
          <div className="total-value">
            <h3>Current Value</h3>
            <span className="value-amount">
              ₹{portfolioMetrics.totalCurrent.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        <div className="summary-metrics">
          <div className="metric-item">
            <label>Total Invested</label>
            <span className="metric-value">
              ₹{portfolioMetrics.totalInvested.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </span>
          </div>

          <div className="metric-item">
            <label>Total Returns</label>
            <span className={`metric-value ${portfolioMetrics.totalReturns >= 0 ? 'positive' : 'negative'}`}>
              {portfolioMetrics.totalReturns >= 0 ? '+' : ''}₹{Math.abs(portfolioMetrics.totalReturns).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              <small>({portfolioMetrics.totalReturnsPercent >= 0 ? '+' : ''}{portfolioMetrics.totalReturnsPercent.toFixed(2)}%)</small>
            </span>
          </div>

          <div className="metric-item">
            <label>Today's Change</label>
            <span className={`metric-value ${portfolioMetrics.totalOneDayChange >= 0 ? 'positive' : 'negative'}`}>
              {portfolioMetrics.totalOneDayChange >= 0 ? '+' : ''}₹{Math.abs(portfolioMetrics.totalOneDayChange).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              <small>({portfolioMetrics.totalOneDayChangePercent >= 0 ? '+' : ''}{portfolioMetrics.totalOneDayChangePercent.toFixed(2)}%)</small>
            </span>
          </div>
        </div>
      </section>

      {/* Holdings List */}
      <section className="holdings-section">
        {holdings.length === 0 ? (
          <div className="no-holdings">
            <div className="empty-state">
              <h3>No Holdings Yet</h3>
              <p>Start building your portfolio by searching and buying stocks from the Home page.</p>
            </div>
          </div>
        ) : (
          <div className="holdings-table-container">
            <table className="holdings-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Market Price</th>
                  <th>Returns</th>
                  <th>Current Value</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding) => {
                  const avgPrice = parsePrice(holding.avgPrice);
                  const marketPrice = parsePrice(holding.marketPrice);
                  const previousClose = parsePrice(holding.previousClose);
                  const quantity = parseInt(holding.quantity, 10) || 0;

                  const totalInvestment = avgPrice * quantity;
                  const currentValue = marketPrice * quantity;
                  const returns = currentValue - totalInvestment;
                  const returnsPercent = totalInvestment > 0 ? (returns / totalInvestment) * 100 : 0;

                  const oneDayChange = (marketPrice - previousClose) * quantity;
                  const oneDayChangePercent = previousClose > 0 ? 
                    ((marketPrice - previousClose) / previousClose) * 100 : 0;

                  return (
                    <tr
                      key={holding.id}
                      className="holding-row"
                      onClick={() => navigate(`/holding-details/${holding.id}`)}
                    >
                      <td className="company-cell">
                        <div className="company-info">
                          <div className="company-name">{holding.name}</div>
                          <div className="company-details">
                            {quantity} shares • Avg ₹{avgPrice.toFixed(2)}
                          </div>
                        </div>
                      </td>

                      <td className="price-cell">
                        <div className="price-info">
                          <span className="market-price">₹{marketPrice.toFixed(2)}</span>
                          <span className={`price-change ${oneDayChange >= 0 ? 'positive' : 'negative'}`}>
                            {oneDayChange >= 0 ? '+' : ''}₹{Math.abs(oneDayChange).toFixed(2)} 
                            ({oneDayChangePercent >= 0 ? '+' : ''}{oneDayChangePercent.toFixed(2)}%)
                          </span>
                        </div>
                      </td>

                      <td className="returns-cell">
                        <div className={`returns-info ${returns >= 0 ? 'positive' : 'negative'}`}>
                          <span className="returns-amount">
                            {returns >= 0 ? '+' : ''}₹{Math.abs(returns).toFixed(2)}
                          </span>
                          <span className="returns-percent">
                            ({returnsPercent >= 0 ? '+' : ''}{returnsPercent.toFixed(2)}%)
                          </span>
                        </div>
                      </td>

                      <td className="value-cell">
                        <div className="value-info">
                          <span className={`current-value ${currentValue >= totalInvestment ? 'positive' : 'negative'}`}>
                            ₹{currentValue.toFixed(2)}
                          </span>
                          <span className="invested-value">
                            Invested: ₹{totalInvestment.toFixed(2)}
                          </span>
                        </div>
                      </td>

                      <td className="actions-cell">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openSellModal(holding);
                          }}
                          className="sell-button"
                        >
                          Sell
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Error Display */}
      {error && (
        <div className="error-section">
          <p className="error-message">{error}</p>
          <button onClick={fetchHoldings} className="retry-button">
            Retry
          </button>
        </div>
      )}

      {/* Sell Modal */}
      {showSellModal && selectedHolding && (
        <div className="modal-overlay" onClick={closeSellModal}>
          <div className="sell-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">
                Sell {selectedHolding.name}
              </h3>
              <button className="modal-close-button" onClick={closeSellModal}>
                ×
              </button>
            </div>

            <div className="modal-body">
              <div className="holding-info">
                <p><strong>Symbol:</strong> {selectedHolding.symbol || selectedHolding.ticker}</p>
                <p><strong>Current Holdings:</strong> {selectedHolding.quantity} shares</p>
                <p><strong>Current Price:</strong> ₹{parsePrice(selectedHolding.marketPrice).toFixed(2)}</p>
              </div>

              <div className="form-group">
                <label htmlFor="sellQuantity" className="form-label">
                  Quantity to Sell
                </label>
                <input
                  id="sellQuantity"
                  type="number"
                  min="1"
                  max={selectedHolding.quantity}
                  placeholder={`Enter 1-${selectedHolding.quantity}`}
                  className="quantity-input"
                  value={sellQuantity}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '' || (parseInt(value, 10) > 0 && parseInt(value, 10) <= selectedHolding.quantity)) {
                      setSellQuantity(value);
                    }
                  }}
                />
              </div>

              {sellQuantity && (
                <div className="sell-preview">
                  <p><strong>Sell Value:</strong> ₹{(parsePrice(selectedHolding.marketPrice) * parseInt(sellQuantity, 10)).toFixed(2)}</p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="cancel-button" onClick={closeSellModal}>
                Cancel
              </button>
              <button 
                className="confirm-sell-button" 
                onClick={handleSellStock}
                disabled={!sellQuantity || parseInt(sellQuantity, 10) <= 0}
              >
                Confirm Sell
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Holdings;
