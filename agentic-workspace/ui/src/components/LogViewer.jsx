import React, { useRef, useEffect, useState } from 'react';
import './LogViewer.css';

export function LogViewer({ logs }) {
  const logContainerRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (!logContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  const getLogLevel = (log) => {
    if (log.level) return log.level;
    if (log.raw) {
      const lowerRaw = log.raw.toLowerCase();
      if (lowerRaw.includes('error') || lowerRaw.includes('fail')) return 'error';
      if (lowerRaw.includes('warn')) return 'warning';
      if (lowerRaw.includes('debug')) return 'debug';
    }
    return 'info';
  };

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    return getLogLevel(log) === filter;
  });

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
      });
    } catch {
      return 'N/A';
    }
  };

  return (
    <div className="log-viewer">
      <div className="log-viewer-header">
        <h3>Real-Time Logs</h3>
        <div className="log-controls">
          <div className="log-filter">
            <button
              className={filter === 'all' ? 'active' : ''}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            <button
              className={filter === 'info' ? 'active' : ''}
              onClick={() => setFilter('info')}
            >
              Info
            </button>
            <button
              className={filter === 'warning' ? 'active' : ''}
              onClick={() => setFilter('warning')}
            >
              Warn
            </button>
            <button
              className={filter === 'error' ? 'active' : ''}
              onClick={() => setFilter('error')}
            >
              Error
            </button>
          </div>
          <button
            className={`auto-scroll-btn ${autoScroll ? 'active' : ''}`}
            onClick={() => setAutoScroll(!autoScroll)}
          >
            {autoScroll ? '🔒 Auto-Scroll' : '🔓 Manual'}
          </button>
        </div>
      </div>
      <div
        ref={logContainerRef}
        className="log-container"
        onScroll={handleScroll}
      >
        {filteredLogs.length === 0 ? (
          <div className="log-empty">
            {filter === 'all'
              ? 'Waiting for logs...'
              : `No ${filter} logs to display`}
          </div>
        ) : (
          filteredLogs.map((log, index) => {
            const level = getLogLevel(log);
            const message = log.message || log.raw || JSON.stringify(log);

            return (
              <div key={index} className={`log-entry log-${level}`}>
                <span className="log-timestamp">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={`log-level log-level-${level}`}>
                  {level.toUpperCase()}
                </span>
                {log.source && (
                  <span className="log-source">[{log.source}]</span>
                )}
                <span className="log-message">{message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
