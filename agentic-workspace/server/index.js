const express = require('express');
const cors = require('cors');
const path = require('path');
const http = require('http');
const { setupWebSocket } = require('./websocket/websocketServer');
const { setupAPIRoutes } = require('./api/routes');
const { logWatcher } = require('./middleware/logWatcher');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

setupAPIRoutes(app);

if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../ui/dist')));
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../ui/dist/index.html'));
  });
}

const wss = setupWebSocket(server);

logWatcher.start(wss);

server.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════════════════╗
║   Agentic Workspace Dashboard Server             ║
╟───────────────────────────────────────────────────╢
║   Server running on: http://localhost:${PORT}      ║
║   WebSocket ready for real-time updates          ║
║   Environment: ${process.env.NODE_ENV || 'development'}                   ║
╚═══════════════════════════════════════════════════╝
  `);
});

process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  logWatcher.stop();
  server.close(() => {
    console.log('HTTP server closed');
  });
});

module.exports = { app, server };
