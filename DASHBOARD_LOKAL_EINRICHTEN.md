# 🚀 Dashboard Lokal Einrichten - Vollständige Anleitung

## 📦 Verfügbare Ressourcen

Ich habe für Sie **5 verschiedene Ressourcen** vorbereitet:

| Ressource | Pfad | Verwendung |
|-----------|------|------------|
| **1. TAR.GZ Archiv** | `/home/user/Valtheron/agentic-dashboard-complete.tar.gz` | ✅ **EMPFOHLEN** für Linux/Mac |
| **2. ZIP Archiv** | `/home/user/Valtheron/agentic-dashboard-complete.zip` | ✅ **EMPFOHLEN** für Windows |
| **3. Komplette Dateiliste** | `/home/user/Valtheron/KOMPLETTE_DATEIEN.txt` | Alle 26 Dateien mit Inhalt (1759 Zeilen) |
| **4. Markdown-Dokumentation** | `/home/user/Valtheron/agentic-workspace/DASHBOARD.md` | Vollständige Dokumentation |
| **5. Test-Script** | `/home/user/Valtheron/agentic-workspace/test-dashboard.js` | API-Tests |

---

## 🎯 METHODE 1: Archiv verwenden (EINFACHSTE METHODE)

### Für Linux/Mac (TAR.GZ):

```bash
# 1. Archiv kopieren zu Ihrem lokalen System
# Datei: /home/user/Valtheron/agentic-dashboard-complete.tar.gz

# 2. Entpacken
tar -xzf agentic-dashboard-complete.tar.gz
cd agentic-workspace

# 3. Dependencies installieren
npm install

# 4. UI Dependencies installieren
cd ui
npm install
cd ..

# 5. Dashboard starten
npm run dev

# 6. Browser öffnen:
# Frontend: http://localhost:5173
# Backend API: http://localhost:3000
```

### Für Windows (ZIP):

```powershell
# 1. ZIP-Datei kopieren
# Datei: /home/user/Valtheron/agentic-dashboard-complete.zip

# 2. Rechtsklick auf ZIP → "Alle extrahieren"

# 3. PowerShell oder CMD öffnen
cd agentic-workspace

# 4. Dependencies installieren
npm install
cd ui
npm install
cd ..

# 5. Dashboard starten
npm run dev

# 6. Browser öffnen: http://localhost:5173
```

---

## 📋 METHODE 2: Manuelle Erstellung aus Dateiliste

Falls Sie die Dateien manuell erstellen möchten:

### Schritt 1: Dateiliste herunterladen

Datei: `/home/user/Valtheron/KOMPLETTE_DATEIEN.txt`

Diese Datei enthält ALLE 26 Dateien mit vollständigem Inhalt:
- 1× Root package.json
- 4× Server-Dateien (Express, API, WebSocket, Log-Watcher)
- 21× UI-Dateien (React Components, Services, Styles)

### Schritt 2: Verzeichnisstruktur erstellen

```bash
mkdir -p agentic-workspace/{server/{api,websocket,middleware},ui/src/{components,hooks,services,styles},logs}
cd agentic-workspace
```

### Schritt 3: Dateien erstellen

Öffnen Sie `/home/user/Valtheron/KOMPLETTE_DATEIEN.txt` und kopieren Sie jeden Dateiabschnitt:

```
===================================================================
DATEI: ./package.json
===================================================================
{
  "name": "agentic-workspace",
  ...
}
```

➡️ Erstellen Sie `package.json` mit dem Inhalt zwischen den Trennlinien

Wiederholen Sie dies für alle 26 Dateien.

---

## 🗂️ Vollständige Dateistruktur

Nach dem Entpacken sollten Sie folgende Struktur haben:

```
agentic-workspace/
├── package.json                                      ← Root Config
├── DASHBOARD.md                                      ← Dokumentation
├── test-dashboard.js                                 ← Test Script
│
├── server/                                           ← Backend (Node.js)
│   ├── index.js                                     ← Hauptserver
│   ├── api/
│   │   └── routes.js                                ← REST API Routen
│   ├── websocket/
│   │   └── websocketServer.js                       ← WebSocket Handler
│   └── middleware/
│       └── logWatcher.js                            ← Log File Monitor
│
├── ui/                                              ← Frontend (React)
│   ├── package.json                                 ← UI Dependencies
│   ├── vite.config.js                               ← Vite Config
│   ├── index.html                                   ← HTML Template
│   ├── .gitignore                                   ← Git Ignore
│   │
│   └── src/
│       ├── main.jsx                                 ← Entry Point
│       ├── App.jsx                                  ← Main App
│       ├── App.css                                  ← App Styles
│       │
│       ├── components/                              ← React Components
│       │   ├── Header.jsx                           ← Header Component
│       │   ├── Header.css                           ← Header Styles
│       │   ├── StatCard.jsx                         ← Statistics Card
│       │   ├── StatCard.css
│       │   ├── LogViewer.jsx                        ← Real-Time Log Viewer
│       │   ├── LogViewer.css
│       │   ├── ConfigList.jsx                       ← Config List
│       │   └── ConfigList.css
│       │
│       ├── hooks/                                   ← Custom Hooks
│       │   └── useWebSocket.js                      ← WebSocket Hook
│       │
│       ├── services/                                ← API Services
│       │   ├── api.js                               ← REST API Client
│       │   └── websocket.js                         ← WebSocket Client
│       │
│       └── styles/                                  ← Global Styles
│           └── index.css                            ← Global CSS
│
└── logs/                                            ← Log Directory (erstellt automatisch)
```

**Gesamt: 26 Dateien**

---

## 🔧 Nach der Installation

### 1. Dashboard starten

```bash
npm run dev
```

**Was passiert:**
- ✅ Backend startet auf `http://localhost:3000`
- ✅ Frontend startet auf `http://localhost:5173`
- ✅ WebSocket-Verbindung wird hergestellt
- ✅ Log-Watcher überwacht `/logs` Verzeichnis

### 2. Im Browser öffnen

```
http://localhost:5173
```

### 3. Test-Logs generieren

```bash
# Öffnen Sie ein neues Terminal
cd agentic-workspace

# Log-Eintrag hinzufügen
echo '{"timestamp":"'$(date -Iseconds)'","level":"info","message":"Test Log!","agent":"demo"}' >> logs/test.json
```

➡️ Der Log erscheint sofort im Dashboard!

### 4. Dashboard stoppen

```bash
# Drücken Sie Ctrl+C im Terminal
# Oder:
pkill -f "npm run dev"
```

---

## 📊 Dashboard-Features

### Header
- **Live-Status-Indikator**: Grün = verbunden, Rot = getrennt
- **Echtzeit-Verbindung**: WebSocket-Status

### Statistik-Karten
- Anzahl Agents, Workflows, Tasks, Tools
- Automatische Updates

### Konfigurations-Listen
- Expandierbare Accordions
- Details zu jedem Agent/Workflow/Task/Tool

### Log-Viewer
- **Echtzeit-Streaming**: Neue Logs erscheinen automatisch
- **Filter**: All, Info, Warn, Error
- **Auto-Scroll**: 🔒 aktiviert / 🔓 deaktiviert
- **Farbcodierung**: Info (blau), Warn (gelb), Error (rot)

---

## 🛠️ Fehlerbehebung

### Problem: "npm: command not found"
**Lösung:** Installieren Sie Node.js 18+
```bash
# Prüfen Sie die Version:
node --version
npm --version
```

### Problem: Port 3000 oder 5173 bereits belegt
**Lösung:** Ändern Sie den Port
```bash
# Backend Port ändern:
PORT=8000 npm run server

# Frontend Port wird automatisch angepasst (Vite fragt nach)
```

### Problem: WebSocket-Verbindung fehlgeschlagen
**Lösung:**
1. Prüfen Sie, ob Backend läuft: `http://localhost:3000/api/health`
2. Firewall-Einstellungen prüfen
3. Browser-Konsole für Fehler prüfen (F12)

### Problem: Logs erscheinen nicht
**Lösung:**
1. Prüfen Sie `/logs` Verzeichnis existiert
2. Log-Dateien müssen `.json` oder `.log` Endung haben
3. JSON-Logs müssen valides JSON sein (ein Objekt pro Zeile)

---

## 📚 Weiterführende Ressourcen

### Dokumentation
- **Dashboard-Dokumentation**: `DASHBOARD.md` im Projekt
- **API-Referenz**: Siehe DASHBOARD.md Abschnitt "API Endpoints"
- **WebSocket-Events**: Siehe DASHBOARD.md Abschnitt "WebSocket Events"

### API-Endpunkte testen
```bash
# Gesundheitscheck
curl http://localhost:3000/api/health

# Statistiken
curl http://localhost:3000/api/stats

# Agents abrufen
curl http://localhost:3000/api/agents

# Logs abrufen
curl http://localhost:3000/api/logs?limit=10
```

### Entwicklung

**Struktur anpassen:**
- Backend: Dateien in `server/`
- Frontend Components: `ui/src/components/`
- Styles: `ui/src/styles/`

**Hot Reload:**
- Frontend: Automatisch (Vite)
- Backend: Neustart erforderlich (Ctrl+C → `npm run dev`)

---

## ✅ Checkliste

- [ ] Node.js 18+ installiert
- [ ] Archiv entpackt ODER Dateien manuell erstellt
- [ ] `npm install` im Root ausgeführt
- [ ] `npm install` in `ui/` ausgeführt
- [ ] `npm run dev` gestartet
- [ ] Browser auf `http://localhost:5173` geöffnet
- [ ] Grüner Status-Indikator sichtbar
- [ ] Statistik-Karten zeigen Werte
- [ ] Log-Viewer funktioniert
- [ ] Test-Log erstellt und erscheint im Dashboard

---

## 🎉 Fertig!

Ihr Dashboard läuft jetzt lokal und ist bereit zur Verwendung!

**Support:**
- Dokumentation: `DASHBOARD.md`
- API-Tests: `test-dashboard.js`
- Alle Dateien: `KOMPLETTE_DATEIEN.txt`

**Viel Erfolg! 🚀**
