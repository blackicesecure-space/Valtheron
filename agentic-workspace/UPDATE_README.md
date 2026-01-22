# Valtheron LLM & CLI Update

Dieses Update-Paket erweitert Valtheron um die Claude-Integration und eine vollständige Kommandozeilen-Schnittstelle.

## Neue Komponenten

### LLM Provider System (`providers/`)

Das Provider-System ermöglicht die Anbindung an verschiedene LLM-Dienste. Die Implementierung für Anthropic/Claude ist vollständig und produktionsreif.

Die Datei `base_provider.py` enthält abstrakte Basisklassen und Interfaces, die für alle Provider gelten. Die Datei `anthropic_provider.py` bietet die vollständige Claude-Integration mit Unterstützung für alle Claude 4.5 Modelle, Tool Use, Streaming und automatische Retry-Logik.

### CLI (`cli/`)

Die Kommandozeilen-Schnittstelle `valtheron.py` bietet folgende Funktionen: Workspace-Initialisierung, Agent-Verwaltung und Task-Ausführung, interaktiver Chat mit Claude (mit Streaming-Option), Workflow-Management, Code-Analyse und Tool-Übersicht.

### Dokumentation (`docs/`)

Die Datei `CLI_AND_LLM_GUIDE.md` enthält eine umfassende Anleitung zur Verwendung der CLI und zur programmatischen Nutzung der LLM-Integration.

## Installation

Kopieren Sie die neuen Ordner (`providers/`, `cli/`, `docs/`) in Ihr bestehendes Valtheron-Repository. Installieren Sie anschließend die Abhängigkeiten mit dem Befehl `pip install -r requirements.txt`. Setzen Sie Ihren Anthropic API-Schlüssel als Umgebungsvariable mit `export ANTHROPIC_API_KEY="ihr-schlüssel"`.

Optional können Sie die CLI global installieren, indem Sie im agentic-workspace Verzeichnis den Befehl `pip install -e .` ausführen.

## Schnellstart

Für einen interaktiven Chat mit Claude führen Sie `python cli/valtheron.py chat` aus. Um verfügbare Agenten aufzulisten, verwenden Sie `python cli/valtheron.py agent list`. Für die Code-Analyse nutzen Sie `python cli/valtheron.py analyze ihre-datei.py`.

## Dateistruktur

```
agentic-workspace/
├── providers/
│   ├── __init__.py
│   ├── base_provider.py
│   └── anthropic_provider.py
├── cli/
│   ├── __init__.py
│   └── valtheron.py
├── docs/
│   └── CLI_AND_LLM_GUIDE.md
├── requirements.txt (aktualisiert)
└── setup.py (neu)
```

## Voraussetzungen

Python 3.10 oder höher wird benötigt. Der Anthropic API-Schlüssel ist für LLM-Funktionen erforderlich und kann unter https://console.anthropic.com bezogen werden.

## Aktualisierungsdatum

22. Januar 2026
