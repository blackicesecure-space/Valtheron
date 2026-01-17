import { useEffect, useState } from 'react';
import { wsService } from '../services/websocket';

export function useWebSocket() {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    wsService.connect();

    const handleConnection = (data) => {
      setConnectionStatus(data.status);
    };

    const handleLog = (data) => {
      setLogs(prevLogs => {
        const newLogs = [data.data, ...prevLogs];
        return newLogs.slice(0, 1000);
      });
    };

    wsService.on('connection', handleConnection);
    wsService.on('log', handleLog);

    return () => {
      wsService.off('connection', handleConnection);
      wsService.off('log', handleLog);
      wsService.disconnect();
    };
  }, []);

  return {
    connectionStatus,
    logs,
    send: wsService.send.bind(wsService)
  };
}
