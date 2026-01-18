#!/bin/bash

# ===================================================================
# AGENTIC WORKSPACE DASHBOARD - COMPLETE SETUP SCRIPT
# ===================================================================
# Dieses Script erstellt ALLE notwendigen Dateien für das Dashboard
# ===================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=============================================="
echo "  Agentic Workspace Dashboard Setup"
echo "=============================================="
echo -e "${NC}"

# Projekt-Verzeichnis
PROJECT_DIR="agentic-workspace-dashboard"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠ Verzeichnis '$PROJECT_DIR' existiert bereits!${NC}"
    read -p "Möchten Sie es löschen und neu erstellen? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
        echo -e "${GREEN}✓ Altes Verzeichnis gelöscht${NC}"
    else
        echo "Abgebrochen."
        exit 1
    fi
fi

echo -e "${BLUE}Erstelle Verzeichnisstruktur...${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Verzeichnisse erstellen
mkdir -p server/api
mkdir -p server/websocket
mkdir -p server/middleware
mkdir -p ui/src/components
mkdir -p ui/src/hooks
mkdir -p ui/src/services
mkdir -p ui/src/styles
mkdir -p logs
mkdir -p agents
mkdir -p workflows
mkdir -p tasks
mkdir -p tools
mkdir -p config

echo -e "${GREEN}✓ Verzeichnisstruktur erstellt${NC}"

# ===================================================================
# ROOT package.json
# ===================================================================
echo -e "${BLUE}Erstelle package.json...${NC}"
cat > package.json << 'EOF'
{
  "name": "agentic-workspace",
  "version": "1.0.0",
  "description": "Comprehensive workspace for AI agent development and deployment",
  "main": "index.js",
  "scripts": {
    "test": "jest",
    "lint": "eslint .",
    "format": "prettier --write .",
    "validate": "node scripts/validate-configs.js",
    "server": "node server/index.js",
    "dev": "concurrently \"npm run server\" \"cd ui && npm run dev\"",
    "build:ui": "cd ui && npm run build"
  },
  "keywords": [
    "ai",
    "agents",
    "automation",
    "workflow",
    "agentic"
  ],
  "author": "",
  "license": "MIT",
  "devDependencies": {
    "eslint": "^8.50.0",
    "jest": "^29.7.0",
    "prettier": "^3.0.3"
  },
  "dependencies": {
    "ajv": "^8.12.0",
    "dotenv": "^16.3.1",
    "js-yaml": "^4.1.0",
    "express": "^4.18.2",
    "ws": "^8.14.2",
    "cors": "^2.8.5",
    "chokidar": "^3.5.3",
    "concurrently": "^8.2.2"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
EOF
echo -e "${GREEN}✓ package.json erstellt${NC}"

# ===================================================================
# SERVER FILES
# ===================================================================
echo -e "${BLUE}Erstelle Server-Dateien...${NC}"

# server/index.js
cat > server/index.js << 'SERVEREOF'
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
  console.log(\`
╔═══════════════════════════════════════════════════╗
║   Agentic Workspace Dashboard Server             ║
╟───────────────────────────────────────────────────╢
║   Server running on: http://localhost:\${PORT}      ║
║   WebSocket ready for real-time updates          ║
║   Environment: \${process.env.NODE_ENV || 'development'}                   ║
╚═══════════════════════════════════════════════════╝
  \`);
});

process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  logWatcher.stop();
  server.close(() => {
    console.log('HTTP server closed');
  });
});

module.exports = { app, server };
SERVEREOF

echo -e "${GREEN}✓ server/index.js${NC}"

# Der Rest des Scripts wird in der nächsten Nachricht fortgesetzt...
echo ""
echo -e "${YELLOW}Script wird fortgesetzt. Bitte warten...${NC}"
EOF

chmod +x "$CREATE_DASHBOARD_SCRIPT"
