// src/pages/HoldingDetails.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function HoldingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [holding, setHolding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch('http://localhost:5000/api/holdings')
      .then(res => res.json())
      .then(data => {
        // match id (both sides as string to be safe)
        const found = data.holdings.find(h => h.id.toString() === id.toString());
        if (found) {
          setHolding(found);
          setError("");
        } else {
          setError("Holding not found");
        }
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to fetch holding data");
        setLoading(false);
      });
  }, [id]);

  const formatDate = (iso) => {
    if (!iso) return "-";
    try {
      const d = new Date(iso);
      return d.toLocaleString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return iso;
    }
  };

  if (loading) return <div style={{ color: 'white', textAlign: 'center', marginTop: '50px' }}>Loading...</div>;
  if (error) return <div style={{ color: 'red', textAlign: 'center', marginTop: '50px' }}>{error}</div>;

  const avgPrice = parseFloat(holding.avgPrice) || 0;
  const marketPrice = parseFloat((holding.marketPrice || "").replace(/[^\d.-]/g, '')) || 0;
  const quantity = holding.quantity || 0;
  const totalInvestment = avgPrice * quantity;
  const currentValue = marketPrice * quantity;
  const returnsValue = currentValue - totalInvestment;
  const returnsPercent = totalInvestment ? (returnsValue / totalInvestment) * 100 : 0;

  return (
    <div style={{ padding: '20px', minHeight: '100vh', color: 'white', maxWidth: '800px', margin: 'auto' }}>
      <button
        onClick={() => navigate(-1)}
        style={{ marginBottom: '20px', cursor: 'pointer', background: '#eb0000ff', color: '#fff', border: 'none', padding: '8px 12px', borderRadius: 6 }}
      >
        ← Back
      </button>

      <h2 style={{ marginBottom: 6 }}>{holding.name} <span style={{ color: '#999', fontSize: 14 }}>({holding.symbol})</span></h2>

      <div style={{ marginBottom: 18, color: '#999' }}>
        <strong>Exchange:</strong> {holding.exchange || '-'} &nbsp; • &nbsp;
        <strong>Purchased:</strong> {formatDate(holding.purchaseDate)}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', color: 'white' }}>
        <tbody>
          <tr style={{ borderBottom: '1px solid #444' }}>
            <td style={{ padding: '10px', fontWeight: 'bold' }}>Quantity</td>
            <td style={{ padding: '10px' }}>{quantity}</td>
          </tr>

          <tr style={{ borderBottom: '1px solid #444' }}>
            <td style={{ padding: '10px', fontWeight: 'bold' }}>Average Buy Price</td>
            <td style={{ padding: '10px' }}>₹{avgPrice.toFixed(2)}</td>
          </tr>

          <tr style={{ borderBottom: '1px solid #444' }}>
            <td style={{ padding: '10px', fontWeight: 'bold' }}>Market Price</td>
            <td style={{ padding: '10px' }}>₹{marketPrice.toFixed(2)}</td>
          </tr>

          <tr style={{ borderBottom: '1px solid #444' }}>
            <td style={{ padding: '10px', fontWeight: 'bold' }}>Total Investment</td>
            <td style={{ padding: '10px' }}>₹{totalInvestment.toFixed(2)}</td>
          </tr>

          <tr style={{ borderBottom: '1px solid #444' }}>
            <td style={{ padding: '10px', fontWeight: 'bold' }}>Current Value</td>
            <td style={{ padding: '10px', color: currentValue >= totalInvestment ? '#00FF00' : '#FF4C4C', fontWeight: 'bold' }}>
              ₹{currentValue.toFixed(2)}
            </td>
          </tr>

          <tr>
            <td style={{ padding: '10px', fontWeight: 'bold' }}>Returns</td>
            <td style={{ padding: '10px', color: returnsValue >= 0 ? '#00FF00' : '#FF4C4C', fontWeight: 'bold' }}>
              {returnsValue >= 0 ? '+' : '-'}₹{Math.abs(returnsValue).toFixed(2)} ({returnsPercent.toFixed(2)}%)
            </td>
          </tr>
        </tbody>
      </table>

      {/* Later: add more detailed sections here (transactions, charts, notes, etc.) */}
    </div>
  );
}

export default HoldingDetails;
