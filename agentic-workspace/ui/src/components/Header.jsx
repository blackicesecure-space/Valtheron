import React from 'react';
import './Header.css';

export function Header({ connectionStatus }) {
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return '#10b981';
      case 'disconnected':
        return '#ef4444';
      case 'failed':
        return '#f59e0b';
      default:
        return '#64748b';
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="header-title">Agentic Workspace</h1>
          <span className="header-subtitle">Real-Time Dashboard</span>
        </div>
        <div className="header-right">
          <div className="connection-status">
            <div
              className="status-indicator"
              style={{ backgroundColor: getStatusColor() }}
            />
            <span className="status-text">
              {connectionStatus === 'connected' ? 'Live' :
               connectionStatus === 'disconnected' ? 'Connecting...' :
               connectionStatus === 'failed' ? 'Connection Failed' : 'Unknown'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
