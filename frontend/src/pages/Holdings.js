import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Holdings() {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [sellQuantity, setSellQuantity] = useState("");

  const navigate = useNavigate();


  useEffect(() => {
    fetchHoldings();
  }, []);

  const fetchHoldings = () => {
    setLoading(true);
    fetch('http://localhost:5000/api/holdings')
      .then(res => res.json())
      .then(data => {
        setHoldings(data.holdings || []);
        setError(""); // Clear error on success
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to fetch holdings");
        setLoading(false);
      });
  };

  const openSellModal = (holding) => {
    setSelectedHolding(holding);
    setSellQuantity("");
    setShowSellModal(true);
  };

  const closeSellModal = () => {
    setShowSellModal(false);
    setSelectedHolding(null);
    setSellQuantity("");
  };

  const confirmSell = () => {
    if (sellQuantity <= 0 || sellQuantity > selectedHolding.quantity) {
      alert(`Please enter a valid quantity (1 - ${selectedHolding.quantity})`);
      return;
    }

    fetch(`http://localhost:5000/api/holdings/${selectedHolding.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sellQuantity }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.message) {
          alert(data.message);
          fetchHoldings();
          closeSellModal();
        } else if (data.error) {
          alert(`Error: ${data.error}`);
        }
      })
      .catch(() => {
        alert('Failed to process sell request');
      });
  };

  const calculateTotal = () => {
    return holdings.reduce((total, holding) => {
      const price = parseFloat(holding.price.replace(/[^\d.-]/g, '')) || 0;
      return total + (price * holding.quantity);
    }, 0);
  };

  if (loading) {
    return <div style={{ color: 'white', textAlign: 'center', marginTop: '50px' }}>Loading holdings...</div>;
  }

  return (
    <div style={{ padding: '20px', minHeight: '100vh' }}>
      <h2 style={{ color: 'white', textAlign: 'center', marginBottom: '30px' }}>My Holdings</h2>

      {holdings.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', marginTop: '50px' }}>
          <p>No holdings yet.</p>
          <p>Go to Home page and buy some stocks!</p>
        </div>
      ) : (
        <>
          <table style={{ 
            width: '80%', 
            color: 'white', 
            borderCollapse: 'collapse', 
            border: '2px solid #444', 
            margin: '0 auto' 
          }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #444' }}>
                <th style={{ textAlign: 'left', padding: '10px' }}>Company</th>
                <th style={{ textAlign: 'right', padding: '10px' }}>Market Price</th>
                <th style={{ textAlign: 'right', padding: '10px' }}>Returns (₹ / %)</th>
                <th style={{ textAlign: 'right', padding: '10px' }}>Current Value</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding, index) => {
                const avgPrice = parseFloat(holding.avgPrice);
                const marketPrice = parseFloat(holding.marketPrice.replace(/[^\d.-]/g, '')) || 0;
                const quantity = holding.quantity;
                const totalInvestment = avgPrice * quantity;
                const currentValue = marketPrice * quantity;
                const returnsValue = currentValue - totalInvestment;
                const returnsPercent = (returnsValue / totalInvestment) * 100;

                return (
                  <tr   
                    key={index}
                    className="clickable-row"
                    style={{ borderBottom: '1px solid #444' }}
                    onClick={() => navigate(`/holding-details/${holding.id}`)}
                  >
                    <td style={{ padding: '15px' }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>{holding.name}</div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        {quantity} shares • Avg. ₹{avgPrice.toFixed(2)}
                      </div>
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      ₹{marketPrice.toFixed(2)}
                    </td>

                    <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', whiteSpace: 'normal', lineHeight: '1.3' }}>
                      {returnsValue >= 0 ? '+' : '-'}₹{Math.abs(returnsValue).toFixed(2)}
                      <br />
                      <span style={{ color: returnsValue >= 0 ? '#00FF00' : '#FF4C4C', fontSize: '0.8rem' }}>
                        ({returnsPercent.toFixed(2)}%)
                      </span>
                    </td>


                    <td style={{ padding: '10px', textAlign: 'right', whiteSpace: 'normal', lineHeight: '1.3' }}>
                      <span style={{ 
                        fontWeight: 'bold', 
                        color: currentValue >= totalInvestment ? '#00FF00' : '#FF4C4C', 
                        fontSize: '1rem' 
                      }}>
                        ₹{currentValue.toFixed(2)}
                      </span>
                      <br />
                      <span style={{ fontSize: '0.9rem', color: '#fff' }}>
                        Invested: ₹{totalInvestment.toFixed(2)}
                      </span>
                    </td>


                  </tr>
                );
              })}
            </tbody>
          </table>

        </>
      )}

      {error && <p style={{ color: '#ff5e5e', textAlign: 'center' }}>{error}</p>}

      {/* Sell Modal */}
      {showSellModal && selectedHolding && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ textAlign: 'center', padding: '30px' }}>
            <h3>Sell {selectedHolding.name} ({selectedHolding.symbol})</h3>
            <p>Current Quantity: {selectedHolding.quantity}</p>
            <label style={{ display: 'block', marginTop: '20px', color: 'white' }}>
              Quantity to Sell:
              <input
                type="number"
                min="1"
                max={selectedHolding.quantity}
                value={sellQuantity}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === "") {
                    setSellQuantity("");
                  } else {
                    const num = Number(value);
                    if (num > 0) {
                      setSellQuantity(num);
                    }
                  }
                }}

                style={{
                  marginLeft: '10px',
                  padding: '5px',
                  width: '100px',
                  background: '#333',
                  color: 'white',
                  border: '1px solid #555',
                  borderRadius: '4px'
                }}
              />
            </label>
            <div style={{ marginTop: '30px' }}>
              <button
                onClick={confirmSell}
                style={{
                  padding: '10px 20px',
                  background: '#ffaa00',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Confirm Sell
              </button>
              <button
                onClick={closeSellModal}
                style={{
                  padding: '10px 20px',
                  background: '#666',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Holdings;