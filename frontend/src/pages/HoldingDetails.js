/**
 * HoldingDetails Component
 * Displays detailed information about a specific stock holding including
 * portfolio metrics, financial ratios, and purchase history
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function HoldingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  // State management
  const [holding, setHolding] = useState(null);
  const [ratios, setRatios] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ratiosLoading, setRatiosLoading] = useState(false);
  const [error, setError] = useState('');
  const [ratiosError, setRatiosError] = useState('');

  // Fetch holding details on component mount
  useEffect(() => {
    fetchHoldingData();
  }, [id]);

  const fetchHoldingData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/holdings');
      const data = await response.json();
      
      const foundHolding = data.holdings.find(h => String(h.id) === String(id));
      
      if (foundHolding) {
        setHolding(foundHolding);
        setError('');
        await fetchFinancialRatios(foundHolding.ticker || foundHolding.symbol);
      } else {
        setError('Holding not found');
      }
    } catch (err) {
      setError('Failed to fetch holding data');
    } finally {
      setLoading(false);
    }
  };

  const fetchFinancialRatios = async (ticker) => {
    if (!ticker) return;

    setRatiosLoading(true);
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
      setRatiosLoading(false);
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

  // Loading and error states
  if (loading) return <div className="details-loading">Loading...</div>;
  if (error) return <div className="details-error">{error}</div>;

  const metrics = calculatePortfolioMetrics();
  const purchases = getPurchaseHistory();
  const groupedRatios = groupFinancialRatios(ratios);

  return (
    <div className="details-container">
      {/* Navigation */}
      <button onClick={() => navigate(-1)} className="back-button">
        ← Back
      </button>

      {/* Header */}
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

      {/* Portfolio Summary */}
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

      {/* Financial Ratios */}
      <section className="ratios-section">
        <h3 className="ratios-title">
          Financial Ratios
          {ratiosLoading && <span className="loading-indicator"> (Loading...)</span>}
        </h3>

        {ratiosError && (
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

        {!ratiosLoading && ratios && (
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

      {/* Purchase History */}
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
