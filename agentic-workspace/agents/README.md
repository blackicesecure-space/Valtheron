# Valtheron Agent Collection

Dieses Paket enthält 200 spezialisierte Agenten für das Valtheron-Framework, konvertiert aus ChatGPT Custom Personas.

## Übersicht

**Gesamtzahl:** 200 Agenten
**Kategorien:** 10 (je 20 Agenten)
**ID-Schema:** VLT-[KATEGORIE]-[HASH] (z.B. VLT-GES-FB22)

## Kategorien

| Code | Kategorie | Modell | Beschreibung |
|------|-----------|--------|--------------|
| GES | Gesundheitsexperten | claude-opus-4-5 | Fitness, Wellness, Therapie |
| ANA | Analytiker | claude-opus-4-5 | Datenanalyse, Research |
| MKT | Marketer | claude-sonnet-4-5 | Marketing, Branding |
| PRO | Produzent | claude-sonnet-4-5 | Produktion, Logistik |
| ENT | Entrepreneur | claude-opus-4-5 | Unternehmensgründung |
| ETR | Entertainer | claude-sonnet-4-5 | Kreative Berufe |
| LEH | Lehrer | claude-sonnet-4-5 | Bildung, Training |
| SCH | Schriftsteller | claude-opus-4-5 | Content, Texte |
| ECO | E-Commerce | claude-sonnet-4-5 | Online-Handel |
| DEV | Entwickler | claude-sonnet-4-5 | Software, Tech |

## Verzeichnisstruktur

```
agents/
├── agent-index.json      # Index aller Agenten
├── GES/                  # Gesundheitsexperten
│   ├── VLT-GES-FB22.json
│   ├── VLT-GES-8CB4.json
│   └── ...
├── ANA/                  # Analytiker
├── MKT/                  # Marketer
├── PRO/                  # Produzent
├── ENT/                  # Entrepreneur
├── ETR/                  # Entertainer
├── LEH/                  # Lehrer
├── SCH/                  # Schriftsteller
├── ECO/                  # E-Commerce
└── DEV/                  # Entwickler
```

## Agent-Konfiguration (Beispiel)

```json
{
  "id": "VLT-GES-FB22",
  "name": "fitness-app-entwickler",
  "display_name": "Fitness-App-Entwickler",
  "type": "specialist",
  "version": "1.0.0",
  "category": "Gesundheitsexperten",
  "description": "Entwickelt mobile Apps...",
  "model": {
    "provider": "anthropic",
    "name": "claude-opus-4-5-20251101",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "system_prompt": "Du bist Fitness-App-Entwickler...",
  "capabilities": ["health-consulting", "wellness-planning"],
  "tools": ["read", "write", "glob", "grep"],
  "config": {
    "max_retries": 3,
    "timeout_seconds": 300,
    "language": "de"
  }
}
```

## Installation

Kopieren Sie den gesamten `agents/` Ordner in Ihr Valtheron-Projekt:

```
Valtheron/
└── agentic-workspace/
    └── agents/
        ├── agent-index.json
        ├── GES/
        ├── ANA/
        └── ...
```

## Verwendung mit der CLI

Nach der Installation können Sie die Agenten über die CLI verwenden:

```bash
# Alle Agenten auflisten
py cli/valtheron.py agent list

# Einen bestimmten Agenten verwenden
py cli/valtheron.py agent run task --agent VLT-GES-FB22 --params '{"query": "..."}'
```

## Agent-Index

Die Datei `agent-index.json` enthält einen vollständigen Index aller Agenten mit ID, Name, Kategorie und Dateipfad für programmatischen Zugriff.

## ID-Verschlüsselung

Die Agent-IDs sind bewusst nicht sequentiell nummeriert, sondern verwenden ein Hash-basiertes Schema für mehr Sicherheit und Flexibilität. Das Format ist `VLT-[KAT]-[HASH]`, wobei KAT ein 3-Buchstaben-Kategorie-Code und HASH ein 4-stelliger alphanumerischer Code ist.

## Metadaten

Jeder Agent enthält Metadaten über seine Herkunft:
- `source`: "ChatGPT-Personas-Import"
- `original_number`: Die ursprüngliche Nummer aus der Quelldatei
- `imported_at`: Importdatum

## Lizenz

Diese Agenten-Konfigurationen sind Teil des Valtheron-Projekts.
