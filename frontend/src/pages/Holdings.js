import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';


function Holdings() {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [sellQuantity, setSellQuantity] = useState("");
  const [liveUpdate, setLiveUpdate] = useState(false); // Live update toggle


  const navigate = useNavigate();

  useEffect(() => {
    fetchHoldings(); // Fetch once when page loads

    let interval;
    if (liveUpdate) {
      interval = setInterval(() => {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();

        // Between 9:00 and 15:30
        if (
          (hours > 9 || (hours === 9 && minutes >= 0)) &&
          (hours < 15 || (hours === 15 && minutes <= 30))
        ) {
          fetchHoldings();
        }
      }, 30000);
    }

    return () => clearInterval(interval);
  }, [liveUpdate]);



  const fetchHoldings = () => {
    setLoading(true);
    fetch('http://localhost:5000/api/holdings')
      .then(res => res.json())
      .then(data => {
        setHoldings(data.holdings || []);
        setError("");
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

  if (loading) {
    return <div style={{ color: 'white', textAlign: 'center', marginTop: '50px' }}>Loading holdings...</div>;
  }

  // Totals calculation inside the component function
  const totalInvested = holdings.reduce((acc, h) => acc + parseFloat(h.avgPrice) * h.quantity, 0);
  const totalCurrent = holdings.reduce(
    (acc, h) => acc + (parseFloat(h.marketPrice.replace(/[^\d.-]/g, '')) || 0) * h.quantity,
    0
  );
  const totalReturns = totalCurrent - totalInvested;
  const totalReturnsPercent = totalInvested ? (totalReturns / totalInvested) * 100 : 0;

  const totalPrevCloseValue = holdings.reduce(
    (acc, h) => acc + (parseFloat(h.previousClose?.replace(/[^\d.-]/g, '')) || 0) * h.quantity,
    0
  );
  const totalOneDayChange = totalCurrent - totalPrevCloseValue;
  const totalOneDayChangePercent = totalPrevCloseValue ? (totalOneDayChange / totalPrevCloseValue) * 100 : 0;


  return (
    <div style={{ padding: '20px', minHeight: '100vh' }}>
      <h2 style={{ color: 'white', textAlign: 'left', marginBottom: '15px', marginLeft: '10%' }}>Holdings</h2>

      {/* Totals block */}
        <div
          style={{
            width: '80%',
            margin: '0 auto 20px auto',
            background: '#0e0e0eff',
            borderRadius: '8px',
            color: 'white',
            fontWeight: 'bold',
          }}
        >
          {/* Top section */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '20px 50px', // equal padding all around
            }}
          >
            <div style={{ lineHeight: '1.5', fontSize: '17px', color: '#bdbcbcff' }}>
              Current Value<br />
              <span style={{ color: '#00FF00', fontSize: '20px' }}>
                ₹{totalCurrent.toFixed(2)}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center' }}>
              <label className="live-switch">
                <input
                  type="checkbox"
                  checked={liveUpdate}
                  onChange={() => setLiveUpdate(!liveUpdate)}
                />
                <span className="live-slider"></span>
              </label>
              <span style={{ color: 'white', marginLeft: '10px' }}>Live Price</span>
            </div>
          </div>

          {/* Divider */}
          <hr
            style={{
              border: 'none',
              borderTop: '2px dotted #383838ff',
              margin: '0 auto',
              width: '92%',
            }}
          />

          {/* Bottom section */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-around',
              textAlign: 'center',
              padding: '20px 0', // matches top section height
            }}
          >
            <div>
              Total Invested<br />
              <span style={{ color: '#ffaa00' }}>
                ₹{totalInvested.toFixed(2)}
              </span>
            </div>
            <div>
              Total Returns<br />
              <span style={{ color: totalReturns >= 0 ? '#00FF00' : '#FF4C4C' }}>
                ₹{totalReturns.toFixed(2)} ({totalReturnsPercent.toFixed(2)}%)
              </span>
            </div>
            <div>
              1-Day Change<br />
              <span
                style={{
                  color: totalOneDayChange >= 0 ? '#00FF00' : '#FF4C4C',
                }}
              >
                ₹{totalOneDayChange.toFixed(2)} (
                {totalOneDayChangePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>




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
                <th style={{ textAlign: 'right', padding: '10px 60px 10px 10px' }}>Current Value</th>
                <th style={{ textAlign: 'center', padding: '10px' }}>Action</th>
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
                const previousClose = parseFloat(holding.previousClose?.replace(/[^\d.-]/g, '')) || 0;
                const oneDayChangeValue = (marketPrice - previousClose) * quantity;
                const oneDayChangePercent = previousClose ? ((marketPrice - previousClose) / previousClose) * 100 : 0;


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
                    <td style={{ padding: '10px', textAlign: 'right', whiteSpace: 'normal', lineHeight: '1.3' }}>
                      <span style={{ fontWeight: 'bold', fontSize: '1rem' }}>
                        ₹{marketPrice.toFixed(2)}
                      </span>
                      <br />
                      <span style={{ fontSize: '0.8rem', color: oneDayChangeValue >= 0 ? '#00FF00' : '#FF4C4C' }}>
                        {oneDayChangeValue >= 0 ? '+' : '-'}₹{Math.abs(oneDayChangeValue).toFixed(2)} ({oneDayChangePercent.toFixed(2)}%)
                      </span>
                    </td>


                    <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', whiteSpace: 'normal', lineHeight: '1.3' }}>
                      {returnsValue >= 0 ? '+' : '-'}₹{Math.abs(returnsValue).toFixed(2)}
                      <br />
                      <span style={{ color: returnsValue >= 0 ? '#00FF00' : '#FF4C4C', fontSize: '0.8rem' }}>
                        ({returnsPercent.toFixed(2)}%)
                      </span>
                    </td>

                    <td style={{ padding: '10px 60px 10px 10px', textAlign: 'right', whiteSpace: 'normal', lineHeight: '1.3' }}>
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

                    <td style={{ textAlign: 'center' }}>
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
        </>
      )}

      {error && <p style={{ color: '#ff5e5e', textAlign: 'center' }}>{error}</p>}

      {showSellModal && selectedHolding && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ textAlign: 'center', padding: '30px', position: 'relative' }}>

            {/* Close button at top-right */}
            <button
              onClick={closeSellModal}
              style={{
                position: 'absolute',
                top: '10px',
                right: '15px',
                background: 'transparent',
                border: 'none',
                fontSize: '20px',
                fontWeight: 'bold',
                color: 'white',
                cursor: 'pointer'
              }}
            >
              ×
            </button>

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
                  padding: '9px 20px',
                  background: '#c73104ff',
                  color: '#fff',
                  fontSize: '15px',
                  border: 'none',
                  borderRadius: '5px',
                  width: '60%',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Sell
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default Holdings;
