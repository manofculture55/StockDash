import { useState } from "react";
import "./App.css";
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Holdings from './pages/Holdings';

function App() {
  const [company, setCompany] = useState("AXISBANK");
  const [exchange, setExchange] = useState("NSE");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");
  const [companyFullName, setCompanyFullName] = useState("");
  const [showBuyModal, setShowBuyModal] = useState(false);

const openModal = () => setShowBuyModal(true);
const closeModal = () => setShowBuyModal(false);

  

  const fetchPrice = () => {
    setPrice(""); setError("");
    fetch(`http://localhost:5000/api/stock-price?company=${company}&exchange=${exchange}`)
      .then(res => res.json())
      .then(data => {
        if (data.price) {
          setPrice(data.price);
          setCompanyFullName(data.name || "");
        } else {
          setError("Price not found");
        }
      })
      .catch(() => setError("Failed to fetch"));
  };

  return (
    <Router>
      <div className="app-dark">

        <div className="title-container">
          <h1 className="title-dark">Stock Market Dashboard</h1>
        </div>

        <nav className="Nav-Bar">
          <Link to="/">
            <button>Home</button>
          </Link>
          <Link to="/Holdings">
            <button>Holdings</button>
          </Link>
        </nav>


        <Routes>
          <Route path="/" element={
            <div>
              <div className="inputs-container">
                <div className="search-group">
                  <svg className="search-icon" aria-hidden="true" viewBox="0 0 24 24">
                    <g>
                      <path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 
                            4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 
                            3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 
                            11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 
                            7.5-7.5-3.365-7.5-7.5z" />
                    </g>
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
                    <button className="card-button" onClick={openModal}>Buy Now</button>
                  </div>
                </div>
              )}

              {error && <p className="error-dark">{error}</p>}
            </div>
          } />

          <Route path="/Holdings" element={<Holdings />} />
          {/* other routes */}
        </Routes>
      </div>
      {showBuyModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2>Purchase Successful</h2>
            <button onClick={closeModal}>Close</button>
          </div>
        </div>
      )}

    </Router>
  );
}


export default App;
