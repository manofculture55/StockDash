import React, { useState, useEffect } from 'react';

function Holdings() {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState(null);
  const [sellQuantity, setSellQuantity] = useState("");

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
          <div style={{
            textAlign: 'center',
            marginBottom: '30px',
            padding: '20px',
            background: '#1f1f1f',
            borderRadius: '10px',
            border: '2px solid #717172'
          }}>
            <h3 style={{ color: '#5B42F3', margin: '0' }}>
              Total Portfolio Value: ₹{calculateTotal().toFixed(2)}
            </h3>
          </div>

          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '20px',
            justifyContent: 'center'
          }}>

            {holdings.map((holding, index) => (
              <div 
                key={index} 
                className="card" 
                style={{ 
                  flex: '1 1 300px',   // Flexible min width
                  maxWidth: '350px',   // Optional: prevents too-wide cards
                  marginBottom: '20px' 
                }}
              >
                <div className="card-details">
                  <p className="text-title">{holding.name}</p>
                  <p style={{ color: '#999', margin: '5px 0' }}>Symbol: {holding.symbol}</p>
                  <p style={{ color: '#999', margin: '5px 0' }}>Exchange: {holding.exchange}</p>
                  <p className="text-body">Buy Price: {holding.price}</p>
                  <p style={{ color: '#999', margin: '5px 0' }}>Quantity: {holding.quantity}</p>
                  <p style={{ color: '#5B42F3', fontWeight: 'bold' }}>
                    Total Investment: ₹{(parseFloat(holding.price.replace(/[^\d.-]/g, '')) * holding.quantity).toFixed(2)}
                  </p>
                  <p style={{ color: '#666', fontSize: '12px', marginTop: '10px' }}>
                    Purchased: {new Date(holding.purchaseDate).toLocaleDateString()}
                  </p>
                  <button
                    onClick={() => openSellModal(holding)}
                    style={{
                      marginTop: '10px',
                      backgroundColor: '#ffaa00',
                      color: 'black',
                      border: 'none',
                      padding: '8px 15px',
                      borderRadius: '5px',
                      cursor: 'pointer'
                    }}
                  >
                    Sell
                  </button>
                </div>
              </div>
            ))}
          </div>
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