import { useState } from "react";
import "./App.css";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Holdings from "./pages/Holdings";
import HoldingDetails from './pages/HoldingDetails';

function App() {
  const [company, setCompany] = useState("SBIN");
  const [exchange, setExchange] = useState("NSE");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");
  const [companyFullName, setCompanyFullName] = useState("");
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [buyQuantity, setBuyQuantity] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [date, setdate] = useState("");
  const [previousClose, setPreviousClose] = useState("");
  



  const openModal = () => {
    setShowBuyModal(true);
    const cleanPrice = price.replace(/[^\d.-]/g, "");
    setBuyPrice(cleanPrice);
  };

  const closeModal = () => {
    setShowBuyModal(false);
    setBuyQuantity("");
    setBuyPrice("");
    setdate("");
  };

  const fetchPrice = () => {
    setPrice("");
    setError("");

    fetch(`http://localhost:5000/api/stock-price?company=${company}&exchange=${exchange}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.price) {
          setPrice(data.price);
          setCompanyFullName(data.name || "");
          setPreviousClose(data.previous_close || "");
        } else {
          setError("Price not found");
        }
      })
      .catch(() => setError("Failed to fetch"));
  };

  const handleBuyStock = () => {
    const qty = parseInt(buyQuantity, 10);
    if (!qty || qty <= 0) {
      alert("Please enter a valid quantity");
      return;
    }

    if (!buyPrice || buyPrice <= 0) {
      alert("Please enter a valid buying price");
      return;
    }

    const holdingData = {
      name: companyFullName || company,
      symbol: company,
      price: `₹${parseFloat(buyPrice).toFixed(2)}`,
      marketPrice: price,
      previousClose: previousClose,
      quantity: buyQuantity,
      exchange: exchange,
      date: date
    };

    fetch("http://localhost:5000/api/holdings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(holdingData),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.message) {
          alert("Stock added to holdings successfully!");
          closeModal();
        } else {
          alert("Error adding stock to holdings");
        }
      })
      .catch(() => {
        alert("Failed to add stock to holdings");
      });
  };

  return (
    <Router>
      <div className="app-dark">
        <div className="title-container">
          <h1 className="title-dark">Stock Market Dashboard</h1>
        </div>

        <nav className="Nav-Bar">
          <Link to="/"><button>Home</button></Link>
          <Link to="/Holdings"><button>Holdings</button></Link>
        </nav>

        <Routes>
          <Route
            path="/"
            element={
              <div>
                <div className="inputs-container">
                  <div className="search-group">
                    <svg className="search-icon" aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 
                              4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 
                              3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 
                              11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 
                              7.5-7.5-3.365-7.5-7.5z" />
                    </svg>
                    <input
                      placeholder="Search"
                      type="search"
                      className="search-input"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                    />
                  </div>

                  <select
                    className="dropdown-dark"
                    value={exchange}
                    onChange={(e) => setExchange(e.target.value)}
                  >
                    <option value="NSE">NSE</option>
                    <option value="BSE">BSE</option>
                  </select>

                  <button className="button-dark" onClick={fetchPrice}>
                    Get Stock Price
                  </button>
                </div>

                {price && (
                  <div className="card-container">
                    <div className="card">
                      <div className="card-details">
                        <p className="text-title">{companyFullName || company}</p>
                        <p className="text-body">Price: {price}</p>
                      </div>
                      <button className="card-button" onClick={openModal}>
                        Buy Now
                      </button>
                    </div>
                  </div>
                )}

                {error && <p className="error-dark">{error}</p>}
              </div>
            }
          />
          <Route path="/Holdings" element={<Holdings />} />
          <Route path="/holding-details/:id" element={<HoldingDetails />} />
        </Routes>
      </div>

      {showBuyModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2>Buy {companyFullName || company}</h2>
            <p>Price: {price}</p>

            <div style={{ margin: "20px 0" }}>
              <label style={{ display: "block", marginBottom: "10px", color: "white" }}>
                Quantity:
                <input
                  type="number"
                  min="1"
                  value={buyQuantity}
                  onChange={(e) => setBuyQuantity(e.target.value)}
                  style={{
                    marginLeft: "10px",
                    padding: "5px",
                    width: "80px",
                    background: "#333",
                    color: "white",
                    border: "1px solid #555",
                    borderRadius: "4px",
                  }}
                />
              </label>

              <label style={{ display: "block", marginBottom: "10px", color: "white" }}>
                Buy Price (₹):
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={buyPrice}
                  onChange={(e) => setBuyPrice(e.target.value)}
                  placeholder="Enter buy price"
                  style={{
                    marginLeft: "10px",
                    padding: "5px",
                    width: "120px",
                    background: "#333",
                    color: "white",
                    border: "1px solid #555",
                    borderRadius: "4px",
                  }}
                />
              </label>
            </div>


            <label style={{ display: "block", marginBottom: "10px", color: "white" }}>
              Date:
              <input
                type="text"
                value={date}
                onChange={(e) => setdate(e.target.value)}
                placeholder="Enter Date (dd-mm-yyyy)"
                style={{
                  marginLeft: "10px",
                  padding: "5px",
                  width: "200px",
                  background: "#333",
                  color: "white",
                  border: "1px solid #555",
                  borderRadius: "4px",
                }}
              />
            </label>


            <div style={{ display: "flex", gap: "10px", justifyContent: "center", marginTop: "20px" }}>
              <button
                onClick={handleBuyStock}
                style={{
                  padding: "10px 20px",
                  background: "#5B42F3",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                }}
              >
                Confirm Buy
              </button>
              <button
                onClick={closeModal}
                style={{
                  padding: "10px 20px",
                  background: "#666",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </Router>
  );
}

export default App;
