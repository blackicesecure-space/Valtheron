import React, { useState } from 'react';
import './ConfigList.css';

export function ConfigList({ title, items, icon, color = '#3b82f6' }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="config-list">
      <div className="config-list-header" onClick={() => setExpanded(!expanded)}>
        <div className="config-list-title">
          <div className="config-icon" style={{ backgroundColor: `${color}20`, color }}>
            {icon}
          </div>
          <span>{title}</span>
          <span className="config-count">{items.length}</span>
        </div>
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
      </div>
      {expanded && (
        <div className="config-list-content">
          {items.length === 0 ? (
            <div className="config-empty">No {title.toLowerCase()} configured</div>
          ) : (
            items.map((item, index) => (
              <div key={index} className="config-item">
                <div className="config-item-header">
                  <span className="config-item-name">
                    {item.name || item.id || item.filename}
                  </span>
                  {item.type && (
                    <span className="config-item-type">{item.type}</span>
                  )}
                </div>
                {item.description && (
                  <div className="config-item-description">
                    {item.description}
                  </div>
                )}
                {item.model && (
                  <div className="config-item-detail">
                    <strong>Model:</strong> {item.model}
                  </div>
                )}
                {item.steps && (
                  <div className="config-item-detail">
                    <strong>Steps:</strong> {item.steps.length}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
