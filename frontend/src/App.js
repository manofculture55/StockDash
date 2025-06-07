import { useState } from "react";
import "./App.css";

function App() {
  const [company, setCompany] = useState("INFY");
  const [exchange, setExchange] = useState("NSE");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");
  const [companyFullName, setCompanyFullName] = useState("");
  

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
    <div className="app-dark">
      <h1 className="title-dark">Stock Market Dashboard</h1>

      <input
        className="input-dark"
        type="text"
        placeholder="Enter company name (e.g. Infosys)"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
      />

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

      {price && (
        <div className="card">
          <div className="card-details">
            <p className="text-title">{companyFullName || company}</p>
            <p className="text-body">Price: {price}</p>
          </div>
          <button className="card-button">Buy Now</button>
        </div>
      )}

      {error && <p className="error-dark">{error}</p>}
    </div>
  );
}

export default App;
