/**
 * HoldingDetails Component
 * Displays detailed information about a specific stock holding including
 * portfolio metrics, financial ratios, and purchase history
 * ENHANCED: Progressive Loading for Better UX
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function HoldingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  // State management - MODIFIED for progressive loading
  const [holding, setHolding] = useState(null);
  const [ratios, setRatios] = useState(null);
  const [basicDataLoaded, setBasicDataLoaded] = useState(false);  // NEW: Track basic data loading
  const [ratiosLoading, setRatiosLoading] = useState(false);
  const [error, setError] = useState('');
  const [ratiosError, setRatiosError] = useState('');

  // MODIFIED: Fetch holding details with progressive loading
  useEffect(() => {
    fetchHoldingData();
  }, [id]);

  // MODIFIED: Separate ratios loading after basic data is shown
  useEffect(() => {
    if (basicDataLoaded && holding && (holding.ticker || holding.symbol)) {
      fetchFinancialRatios(holding.ticker || holding.symbol);
    }
  }, [basicDataLoaded, holding]);

  const fetchHoldingData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/holdings');
      const data = await response.json();
      
      const foundHolding = data.holdings.find(h => String(h.id) === String(id));
      
      if (foundHolding) {
        setHolding(foundHolding);
        setError('');
        setBasicDataLoaded(true);  // NEW: Mark basic data as loaded immediately
      } else {
        setError('Holding not found');
      }
    } catch (err) {
      setError('Failed to fetch holding data');
    }
  };

  const fetchFinancialRatios = async (ticker) => {
    if (!ticker) return;

    setRatiosLoading(true);  // Show loader
    setRatiosError('');

    try {
      const response = await fetch(`http://localhost:5000/api/stock-ratios/${ticker.toUpperCase()}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        setRatiosError(`Unable to fetch ratios: ${response.status}`);
        return;
      }

      const data = await response.json();
      
      if (data.ratios && Object.keys(data.ratios).length > 0) {
        setRatios(data.ratios);
      } else {
        setRatiosError('No financial ratios available');
      }
    } catch (err) {
      setRatiosError(`Network error: ${err.message}`);
    } finally {
      setRatiosLoading(false);  // Hide loader
    }
  };

  // Helper function to parse numeric values safely
  const parseNumericValue = (value, fallback = 0) => {
    if (typeof value === 'number') return value;
    const cleaned = String(value || '').replace(/[^\d.-]/g, '');
    return parseFloat(cleaned) || fallback;
  };

  // Calculate portfolio metrics
  const calculatePortfolioMetrics = () => {
    const avgPrice = parseNumericValue(holding?.avgPrice);
    const marketPrice = parseNumericValue(holding?.marketPrice);
    const quantity = holding?.quantity || 0;
    const totalInvestment = avgPrice * quantity;
    const currentValue = marketPrice * quantity;
    const returns = currentValue - totalInvestment;
    const returnPercent = totalInvestment ? (returns / totalInvestment) * 100 : 0;

    return {
      avgPrice,
      marketPrice,
      quantity,
      totalInvestment,
      currentValue,
      returns,
      returnPercent
    };
  };

  // Normalize purchase history data
  const getPurchaseHistory = () => {
    const rawPurchases = holding?.purchases || holding?.transactions || [];
    
    return rawPurchases.map(purchase => ({
      date: purchase.date || '',
      quantity: purchase.quantity ?? purchase.qty ?? 0,
      price: parseNumericValue(purchase.price)
    }));
  };

  // Group financial ratios by category
  const groupFinancialRatios = (ratiosData) => {
    if (!ratiosData) return {};

    const categories = {
      valuation: ['Market Cap', 'Current Price', 'Stock P/E', 'Price to book value', 'Price to Sales', 'PEG Ratio'],
      profitability: ['ROE', 'ROCE', 'Profit growth', 'Sales growth', 'Earnings yield'],
      financial: ['Debt', 'Debt to equity', 'Current ratio', 'Book Value', 'EPS', 'Face Value'],
      others: ['High / Low', 'Dividend Yield', 'CMP / FCF']
    };

    const grouped = { valuation: {}, profitability: {}, financial: {}, others: {} };

    Object.entries(ratiosData).forEach(([key, value]) => {
      if (categories.valuation.includes(key)) {
        grouped.valuation[key] = value;
      } else if (categories.profitability.includes(key)) {
        grouped.profitability[key] = value;
      } else if (categories.financial.includes(key)) {
        grouped.financial[key] = value;
      } else {
        grouped.others[key] = value;
      }
    });

    return grouped;
  };

  // MODIFIED: Loading and error states - Progressive approach
  if (!basicDataLoaded && !holding) {
    return <div className="details-loading">Loading...</div>;
  }
  
  if (error) {
    return <div className="details-error">{error}</div>;
  }

  const metrics = calculatePortfolioMetrics();
  const purchases = getPurchaseHistory();
  const groupedRatios = groupFinancialRatios(ratios);

  return (
    <div className="details-container">
      {/* Navigation */}
      <button onClick={() => navigate(-1)} className="back-button">
        ← Back
      </button>

      {/* Header - Shows immediately when basic data loads */}
      <header className="details-header">
        <h2 className="details-title">
          {holding.name}
          <span className="details-symbol">
            ({holding.symbol || holding.ticker})
          </span>
        </h2>
        <div className="exchange-info">
          <strong>Exchange:</strong> {holding.exchange || 'N/A'}
        </div>
      </header>

      {/* Portfolio Summary - Shows immediately when basic data loads */}
      <section className="portfolio-summary">
        <table className="details-table">
          <tbody>
            <tr className="section-header">
              <td colSpan="2">Portfolio Summary</td>
            </tr>
            <tr>
              <td className="details-label">Quantity</td>
              <td className="details-value">{metrics.quantity}</td>
            </tr>
            <tr>
              <td className="details-label">Average Buy Price</td>
              <td className="details-value">₹{metrics.avgPrice.toFixed(2)}</td>
            </tr>
            <tr>
              <td className="details-label">Market Price</td>
              <td className="details-value">₹{metrics.marketPrice.toFixed(2)}</td>
            </tr>
            <tr>
              <td className="details-label">Previous Close</td>
              <td className="details-value">
                ₹{parseNumericValue(holding?.previousClose).toFixed(2)}
              </td>
            </tr>
            <tr>
              <td className="details-label">Total Investment</td>
              <td className="details-value">₹{metrics.totalInvestment.toFixed(2)}</td>
            </tr>
            <tr>
              <td className="details-label">Current Value</td>
              <td className={`details-value ${metrics.currentValue >= metrics.totalInvestment ? 'positive' : 'negative'}`}>
                ₹{metrics.currentValue.toFixed(2)}
              </td>
            </tr>
            <tr>
              <td className="details-label">Returns</td>
              <td className={`details-value ${metrics.returns >= 0 ? 'positive' : 'negative'}`}>
                {metrics.returns >= 0 ? '+' : ''}₹{metrics.returns.toFixed(2)} ({metrics.returnPercent.toFixed(2)}%)
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* Purchase History - Shows immediately when basic data loads */}
      {purchases.length > 0 && (
        <section className="purchase-history-section">
          <table className="details-table">
            <tbody>
              <tr className="section-header">
                <td colSpan="2">Purchase History</td>
              </tr>
              <tr>
                <td colSpan="2" className="purchase-history-container">
                  <table className="purchase-history-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Quantity</th>
                        <th>Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {purchases.map((purchase, index) => (
                        <tr key={index}>
                          <td>{purchase.date}</td>
                          <td>{purchase.quantity}</td>
                          <td>₹{purchase.price.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      )}

      {/* Financial Ratios - MODIFIED: Progressive loading with custom loader */}
      <section className={`ratios-section ${ratiosLoading ? 'loading-glow-border' : ''}`}>
        {/* Only show title when NOT loading */}
        {!ratiosLoading && (
          <h3 className="ratios-title">Financial Ratios</h3>
        )}

        {/* Just the animated loader - no title when loading */}
        {ratiosLoading && (
          <div className="loader">
            <p>loading</p>
            <div className="words">
              <span className="word">Report</span>
              <span className="word">Ratios</span>
              <span className="word">Data</span>
              <span className="word">Summary</span>
              <span className="word">Suggestions</span>
            </div>
          </div>
        )}

        {/* Show error if ratios failed to load */}
        {ratiosError && !ratiosLoading && (
          <div className="ratios-error">
            <strong>Error:</strong> {ratiosError}
            <button 
              onClick={() => fetchFinancialRatios(holding.ticker || holding.symbol)}
              className="retry-button"
            >
              Retry
            </button>
          </div>
        )}

        {/* Show ratios when loaded successfully */}
        {!ratiosLoading && ratios && !ratiosError && (
          <div className="ratios-grid">
            <RatioCategory 
              title="Valuation" 
              ratios={groupedRatios.valuation} 
            />
            <RatioCategory 
              title="Profitability" 
              ratios={groupedRatios.profitability} 
            />
            <RatioCategory 
              title="Financial Health" 
              ratios={groupedRatios.financial} 
            />
            <RatioCategory 
              title="Other Metrics" 
              ratios={groupedRatios.others} 
            />
          </div>
        )}
      </section>

    </div>
  );
}

/**
 * RatioCategory Component
 * Renders a category of financial ratios in a table format
 */
function RatioCategory({ title, ratios }) {
  if (!ratios || Object.keys(ratios).length === 0) {
    return null;
  }

  return (
    <div className="ratio-category">
      <h4 className="category-title">
        {title} ({Object.keys(ratios).length})
      </h4>
      <table className="ratios-table">
        <tbody>
          {Object.entries(ratios).map(([key, value]) => (
            <tr key={key} className="ratio-row">
              <td className="ratio-label">{key}</td>
              <td className="ratio-value">{value?.full_value || 'N/A'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default HoldingDetails;
