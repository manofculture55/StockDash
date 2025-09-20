/**
 * Complete Theme Management System
 * Combines Theme Context Provider with Toggle Component
 * Manages dark/light theme state and provides toggle UI
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

// ============================================================================
// THEME CONTEXT
// ============================================================================

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  // Initialize theme from localStorage or default to 'dark'
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('stock-dashboard-theme');
    return savedTheme || 'dark';
  });

  // Apply theme to document and save to localStorage
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('stock-dashboard-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  const value = {
    theme,
    toggleTheme,
    isDark: theme === 'dark',
    isLight: theme === 'light'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// ============================================================================
// THEME TOGGLE COMPONENT
// ============================================================================

export const ThemeToggle = () => {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <div className="theme-toggle-container">
      <button 
        className={`theme-toggle ${isDark ? 'dark' : 'light'}`}
        onClick={toggleTheme}
        aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        title={`Current: ${theme} mode`}
      >
        <div className="toggle-track">
          <div className="toggle-thumb">
            <div className="toggle-icon">
              {isDark ? (
                // Moon icon
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                  <path d="M21.64,13a1,1,0,0,0-1.05-.14,8.05,8.05,0,0,1-3.37.73A8.15,8.15,0,0,1,9.08,5.49a8.59,8.59,0,0,1,.25-2A1,1,0,0,0,8,2.36,10.14,10.14,0,1,0,22,14.05,1,1,0,0,0,21.64,13Zm-9.5,6.69A8.14,8.14,0,0,1,7.08,5.22v.27A10.15,10.15,0,0,0,17.22,15.63a9.79,9.79,0,0,0,2.1-.22A8.11,8.11,0,0,1,12.14,19.73Z"/>
                </svg>
              ) : (
                // Sun icon
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                  <path d="M5.64,17l-.71.71a1,1,0,0,0,0,1.41,1,1,0,0,0,1.41,0l.71-.71A1,1,0,0,0,5.64,17ZM5,12a1,1,0,0,0-1-1H3a1,1,0,0,0,0,2H4A1,1,0,0,0,5,12Zm7-7a1,1,0,0,0,1-1V3a1,1,0,0,0-2,0V4A1,1,0,0,0,12,5ZM5.64,7.05a1,1,0,0,0,.7.29,1,1,0,0,0,.71-.29,1,1,0,0,0,0-1.41l-.71-.71A1,1,0,0,0,4.93,6.34Zm12,.29a1,1,0,0,0,.7-.29l.71-.71a1,1,0,1,0-1.41-1.41L17,5.64a1,1,0,0,0,0,1.41A1,1,0,0,0,17.66,7.34ZM21,11H20a1,1,0,0,0,0,2h1a1,1,0,0,0,0-2Zm-9,8a1,1,0,0,0-1,1v1a1,1,0,0,0,2,0V20A1,1,0,0,0,12,19ZM18.36,17A1,1,0,0,0,17,18.36l.71.71a1,1,0,0,0,1.41,0,1,1,0,0,0,0-1.41ZM12,6.5A5.5,5.5,0,1,0,17.5,12,5.51,5.51,0,0,0,12,6.5Zm0,9A3.5,3.5,0,1,1,15.5,12,3.5,3.5,0,0,1,12,15.5Z"/>
                </svg>
              )}
            </div>
          </div>
        </div>
      </button>
      <span className="theme-label">
        {isDark ? 'Dark' : 'Light'}
      </span>
    </div>
  );
};

// ============================================================================
// THEME TOGGLE STYLES (Inline CSS-in-JS for single file solution)
// ============================================================================

// Inject styles into document head when component mounts
if (typeof document !== 'undefined') {
  const styleId = 'theme-toggle-styles';
  
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      /* Theme Toggle Component Styles */
      .theme-toggle-container {
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: InterVariable, Inter, sans-serif;
      }

      .theme-toggle {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
      }

      .theme-toggle:hover {
        background: var(--hover-bg);
      }

      .toggle-track {
        width: 44px;
        height: 24px;
        background: var(--toggle-track-bg);
        border-radius: 12px;
        border: 1px solid var(--toggle-border);
        position: relative;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }

      .toggle-thumb {
        width: 18px;
        height: 18px;
        background: var(--toggle-thumb-bg);
        border-radius: 50%;
        position: absolute;
        top: 2px;
        left: 2px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }

      .theme-toggle.dark .toggle-thumb {
        transform: translateX(20px);
        background: var(--toggle-thumb-bg-dark);
      }

      .toggle-icon {
        color: var(--toggle-icon-color);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
      }

      .theme-toggle.dark .toggle-icon {
        color: var(--toggle-icon-color-dark);
      }

      .theme-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-family: InterVariable, Inter, sans-serif;
      }

      /* Animation for icon rotation */
      .theme-toggle.light .toggle-icon {
        animation: rotate-sun 0.5s ease-in-out;
      }

      .theme-toggle.dark .toggle-icon {
        animation: rotate-moon 0.5s ease-in-out;
      }

      @keyframes rotate-sun {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(180deg); }
      }

      @keyframes rotate-moon {
        0% { transform: rotate(180deg); }
        100% { transform: rotate(0deg); }
      }
    `;
    document.head.appendChild(style);
  }
}

export default ThemeToggle;
