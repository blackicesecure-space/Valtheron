# Agentic Workspace Dashboard

Real-time monitoring dashboard for the Agentic Workspace AI Agent Framework.

## Features

- **Real-Time Monitoring**: WebSocket-based live log streaming
- **Configuration Overview**: View all agents, workflows, tasks, and tools
- **Statistics Dashboard**: Quick overview of workspace resources
- **Log Filtering**: Filter logs by level (info, warning, error, debug)
- **Auto-Scroll**: Automatic scrolling for new log entries
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

### Backend (Node.js/Express)
- **Server**: Express.js server with WebSocket support
- **API Endpoints**: REST API for workspace data
- **Log Watcher**: Real-time file system monitoring with chokidar
- **WebSocket**: Live log streaming to connected clients

### Frontend (React/Vite)
- **Framework**: React 18 with Vite build tool
- **Real-Time Updates**: WebSocket integration for live data
- **Components**: Modular dashboard components
- **Styling**: CSS with custom properties (dark theme)

## Installation

### 1. Install Dependencies

```bash
# Install root dependencies
npm install

# Install UI dependencies
cd ui
npm install
cd ..
```

### 2. Start the Dashboard

**Development Mode** (with hot reload):

```bash
npm run dev
```

This starts:
- Backend server on `http://localhost:3000`
- Frontend dev server on `http://localhost:5173`

**Production Mode**:

```bash
# Build the frontend
npm run build:ui

# Start the server
NODE_ENV=production npm run server
```

Access the dashboard at `http://localhost:3000`

## Usage

### Viewing Real-Time Logs

1. Start the dashboard server
2. Open your browser to `http://localhost:5173` (dev) or `http://localhost:3000` (prod)
3. Logs will appear automatically as they are generated

### Running Agents

When you execute agents or workflows, their logs will automatically stream to the dashboard:

```bash
# In another terminal
cd /path/to/agentic-workspace
python examples/simple-agent-example.py
```

### Log Filtering

Use the filter buttons to show only specific log levels:
- **All**: Show all logs
- **Info**: Information messages
- **Warn**: Warning messages
- **Error**: Error messages

### Auto-Scroll

- **Enabled** (🔒): Automatically scrolls to show new logs
- **Disabled** (🔓): Allows manual scrolling through history

## API Endpoints

### GET /api/health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00.000Z",
  "uptime": 1234.56
}
```

### GET /api/workspace/config
Get workspace configuration

### GET /api/agents
List all configured agents

### GET /api/workflows
List all configured workflows

### GET /api/tasks
List all configured tasks

### GET /api/tools
List all configured tools

### GET /api/logs?limit=100
Get recent logs (default: 100 entries)

### GET /api/stats
Get workspace statistics

**Response:**
```json
{
  "agents": 3,
  "workflows": 2,
  "tasks": 4,
  "tools": 5,
  "timestamp": "2026-01-15T10:30:00.000Z"
}
```

## WebSocket Events

### Client → Server

**Ping:**
```json
{
  "type": "ping"
}
```

### Server → Client

**Connection:**
```json
{
  "type": "connection",
  "message": "Connected to Agentic Workspace Dashboard",
  "timestamp": 1705318200000
}
```

**Pong:**
```json
{
  "type": "pong",
  "timestamp": 1705318200000
}
```

**Log Entry:**
```json
{
  "type": "log",
  "data": {
    "timestamp": "2026-01-15T10:30:00.000Z",
    "level": "info",
    "message": "Agent execution started",
    "source": "agent-logs.json"
  },
  "timestamp": 1705318200000
}
```

## Directory Structure

```
agentic-workspace/
├── server/                 # Backend server
│   ├── index.js           # Main server entry
│   ├── api/
│   │   └── routes.js      # API endpoints
│   ├── websocket/
│   │   └── websocketServer.js  # WebSocket handler
│   └── middleware/
│       └── logWatcher.js  # Log file monitor
├── ui/                    # Frontend React app
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API and WebSocket services
│   │   ├── styles/        # CSS stylesheets
│   │   ├── App.jsx        # Main App component
│   │   └── main.jsx       # React entry point
│   ├── index.html         # HTML template
│   ├── vite.config.js     # Vite configuration
│   └── package.json       # UI dependencies
└── package.json           # Root dependencies
```

## Configuration

### Port Configuration

Change the server port by setting the `PORT` environment variable:

```bash
PORT=8080 npm run server
```

### Log Directory

The dashboard monitors the `logs/` directory by default. Logs can be in JSON or plain text format.

**JSON Log Format:**
```json
{
  "timestamp": "2026-01-15T10:30:00.000Z",
  "level": "info",
  "message": "Agent execution started",
  "agent": "task-executor"
}
```

**Plain Text Format:**
```
[2026-01-15 10:30:00] INFO: Agent execution started
```

## Troubleshooting

### WebSocket Connection Issues

1. Check that the server is running: `http://localhost:3000/api/health`
2. Verify no firewall is blocking WebSocket connections
3. Check browser console for connection errors

### Logs Not Appearing

1. Ensure logs are being written to the `logs/` directory
2. Check file permissions on the logs directory
3. Verify log files end with `.json` or `.log` extension

### Build Issues

```bash
# Clean and reinstall dependencies
rm -rf node_modules ui/node_modules
rm package-lock.json ui/package-lock.json
npm install
cd ui && npm install
```

## Development

### Adding New Components

1. Create component file: `ui/src/components/NewComponent.jsx`
2. Create styles: `ui/src/components/NewComponent.css`
3. Import and use in `App.jsx`

### Adding New API Endpoints

1. Add route in `server/api/routes.js`
2. Update API service: `ui/src/services/api.js`
3. Use in React components

### Customizing Theme

Edit CSS variables in `ui/src/styles/index.css`:

```css
:root {
  --primary-bg: #0f172a;
  --accent-blue: #3b82f6;
  /* ... */
}
```

## Performance

- Dashboard handles up to 1000 log entries in memory
- Older logs are automatically discarded
- WebSocket messages are throttled to prevent overwhelming clients
- File watching uses efficient change detection

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## License

MIT
