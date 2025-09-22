/**
 * Login Component with Aurora Background
 * Beautiful login form with flowing aurora lighting effects
 */

import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import Aurora from './Aurora';
import './auth.css';

const Login = () => {
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username.trim() || !formData.password.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');

    const result = await login(formData.username.trim(), formData.password);

    if (result.success) {
      // Login successful - AuthContext will handle the redirect
    } else {
      setError(result.error || 'Login failed');
    }

    setLoading(false);
  };

  // Dynamic import to avoid circular dependency
  if (showRegister) {
    const Register = require('./Register').default;
    return <Register onBackToLogin={() => setShowRegister(false)} />;
  }

  return (
    <div className="auth-container">
      {/* Aurora Background with beautiful flowing colors */}
      <Aurora
        colorStops={["#5227FF", "#FF94B4", "#3A29FF"]}
        blend={0.6}
        amplitude={1.2}
        speed={0.3}
      />
      
      <div className="auth-wrapper">
        <div className="auth-card">
          <div className="auth-header">
            <h1 className="auth-title">Welcome to StockDash</h1>
            <p className="auth-subtitle">Sign in to your portfolio</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            {error && (
              <div className="auth-error">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="username" className="form-label">
                Username or Email
              </label>
              <input
                id="username"
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                className="form-input"
                placeholder="Enter your username or email"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                id="password"
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="form-input"
                placeholder="Enter your password"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className={`auth-button ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => setShowRegister(true)}
                className="auth-link-button"
              >
                Create Account
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
