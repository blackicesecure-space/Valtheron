#!/bin/bash
# Dashboard Setup Script
# Dieses Script erstellt alle notwendigen Dateien für das Agentic Workspace Dashboard

set -e

echo "======================================"
echo "Agentic Workspace Dashboard Setup"
echo "======================================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Basis-Verzeichnis erstellen
WORKSPACE_DIR="agentic-workspace"

if [ -d "$WORKSPACE_DIR" ]; then
    echo -e "${BLUE}Warnung: Verzeichnis $WORKSPACE_DIR existiert bereits${NC}"
    read -p "Möchten Sie fortfahren? Dies überschreibt Dashboard-Dateien. (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

echo -e "${GREEN}✓${NC} Verzeichnisstruktur wird erstellt..."

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

echo -e "${GREEN}✓${NC} Alle Verzeichnisse erstellt"
echo ""
echo "Jetzt kopieren Sie bitte die Dateien aus den folgenden Abschnitten..."
echo "Eine vollständige Dateiliste folgt unten."
