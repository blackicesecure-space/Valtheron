# Valtheron CLI & LLM Integration Guide

Diese Dokumentation erklärt die Verwendung der Valtheron CLI und die Integration mit Claude.

## Installation

Navigieren Sie zunächst in das `agentic-workspace` Verzeichnis und installieren Sie die Abhängigkeiten:

```bash
cd agentic-workspace
pip install -r requirements.txt
```

Für eine systemweite Installation der CLI:

```bash
pip install -e .
```

Nach der Installation ist der `valtheron` Befehl global verfügbar.

## Konfiguration

### API-Schlüssel einrichten

Die LLM-Integration erfordert einen Anthropic API-Schlüssel. Setzen Sie diesen als Umgebungsvariable:

Unter Linux/macOS:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

Unter Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

Für dauerhafte Konfiguration fügen Sie die Variable zu Ihrer Shell-Konfiguration hinzu (`.bashrc`, `.zshrc`, oder Systemumgebungsvariablen unter Windows).

## CLI-Befehle

### Workspace initialisieren

Erstellt eine neue Workspace-Struktur mit allen notwendigen Verzeichnissen:

```bash
valtheron init mein-projekt
cd mein-projekt
```

### Agenten verwalten

Listet alle registrierten Agenten auf:

```bash
valtheron agent list
```

Führt eine Aufgabe mit einem Agenten aus:

```bash
valtheron agent run analyze_code --agent researcher-001 --params '{"path": "./src"}'
```

### Interaktiver Chat mit Claude

Startet einen interaktiven Chat:

```bash
valtheron chat
```

Mit Streaming-Ausgabe (Antworten werden Zeichen für Zeichen angezeigt):

```bash
valtheron chat --stream
```

Mit benutzerdefiniertem System-Prompt:

```bash
valtheron chat --system "Du bist ein Python-Experte. Antworte prägnant."
```

### Workflows verwalten

Listet verfügbare Workflows auf:

```bash
valtheron workflow list
```

Führt einen Workflow aus:

```bash
valtheron workflow run code-review --inputs '{"repository": "./src"}'
```

Mit paralleler Ausführung und ausführlicher Ausgabe:

```bash
valtheron workflow run code-review --parallel --verbose
```

### Code-Analyse

Analysiert eine Datei auf Komplexität, Sicherheit und Performance:

```bash
valtheron analyze main.py
```

Mit spezifischem Analyse-Typ:

```bash
valtheron analyze main.py --type security
valtheron analyze app.js --language javascript --type performance
```

### Tools auflisten

Zeigt alle verfügbaren Tools an:

```bash
valtheron tool list
```

### Version anzeigen

Zeigt Versionsinformationen und verfügbare Komponenten:

```bash
valtheron version
```

## Programmatische Verwendung

### LLM-Provider direkt nutzen

```python
from providers.anthropic_provider import create_claude_client

# Client erstellen
client = create_claude_client(
    model="claude-sonnet-4-5-20250929",
    temperature=0.7
)

# Einfache Anfrage
response = client.chat("Erkläre mir Rekursion in Python.")
print(response.content)
```

### Mit Streaming

```python
from providers.base_provider import LLMMessage

messages = [
    LLMMessage.system("Du bist ein hilfreicher Assistent."),
    LLMMessage.user("Schreibe ein kurzes Gedicht über Code.")
]

for chunk in client.stream(messages):
    print(chunk, end="", flush=True)
```

### Tool Use mit Claude

```python
from providers.base_provider import ToolDefinition, ToolCall, ToolResult

# Tool definieren
calculator_tool = ToolDefinition(
    name="calculator",
    description="Führt mathematische Berechnungen durch",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematischer Ausdruck"
            }
        },
        "required": ["expression"]
    }
)

# Tool-Executor definieren
def execute_tool(tool_call: ToolCall) -> ToolResult:
    if tool_call.name == "calculator":
        try:
            result = eval(tool_call.arguments["expression"])
            return ToolResult(tool_call_id=tool_call.id, output=result)
        except Exception as e:
            return ToolResult(tool_call_id=tool_call.id, output=None, error=str(e))
    return ToolResult(tool_call_id=tool_call.id, output=None, error="Unknown tool")

# Chat mit Tool-Unterstützung
response = client.chat(
    user_message="Was ist 42 * 17?",
    tools=[calculator_tool],
    tool_executor=execute_tool
)
print(response.content)
```

### Agenten mit LLM verbinden

```python
from utils.agent_orchestrator import AgentOrchestrator, AgentConfig
from providers.anthropic_provider import create_claude_client

# Provider erstellen
provider = create_claude_client()

# Orchestrator initialisieren
orchestrator = AgentOrchestrator(agents_dir="./agents")
orchestrator.load_agents()

# Task ausführen
result = orchestrator.execute_task(
    name="analyze",
    action="codebase-analysis",
    params={"path": "./src"}
)

print(f"Status: {result.status}")
print(f"Ergebnis: {result.result}")
```

### Workflow mit LLM-Unterstützung

```python
from utils.workflow_engine import WorkflowEngine

workflow = {
    "name": "code-review",
    "steps": [
        {
            "name": "analyze",
            "agent": "researcher-001",
            "action": "analyze_code",
            "params": {"path": "${inputs.file}"}
        },
        {
            "name": "summarize",
            "agent": "planner-001", 
            "action": "create_summary",
            "params": {"analysis": "${steps.analyze.output}"},
            "depends_on": ["analyze"]
        }
    ]
}

engine = WorkflowEngine()
result = engine.execute(workflow, inputs={"file": "main.py"})
print(f"Workflow Status: {result.status.value}")
```

## Modell-Auswahl

Die verfügbaren Claude-Modelle und ihre Stärken:

**claude-opus-4-5-20251101** eignet sich für komplexe Reasoning-Aufgaben, tiefgreifende Analysen und Research. Es ist das leistungsfähigste Modell.

**claude-sonnet-4-5-20250929** ist der empfohlene Standard für die meisten Aufgaben. Es bietet eine gute Balance zwischen Leistung und Geschwindigkeit.

**claude-haiku-4-5-20251001** ist optimal für schnelle, einfache Aufgaben wie Klassifikation, Extraktion und High-Volume-Operationen.

Sie können Aliases verwenden: `opus`, `sonnet`, `haiku`.

## Fehlerbehandlung

Bei API-Fehlern implementiert der Provider automatische Retries mit exponentiellem Backoff. Die Standardeinstellungen sind 3 Versuche mit 120 Sekunden Timeout.

Für robuste Anwendungen empfiehlt sich zusätzliche Fehlerbehandlung:

```python
from providers.anthropic_provider import AnthropicAPIError

try:
    response = client.chat("Hallo!")
except AnthropicAPIError as e:
    print(f"API-Fehler: {e}")
    print(f"Status Code: {e.status_code}")
except ImportError:
    print("anthropic-Paket nicht installiert")
```

## Umgebungsvariablen

**ANTHROPIC_API_KEY** ist der API-Schlüssel für die Anthropic API (erforderlich).

**VALTHERON_LOG_LEVEL** definiert das Log-Level und kann auf DEBUG, INFO, WARNING oder ERROR gesetzt werden.

**VALTHERON_CONFIG_PATH** ist ein optionaler Pfad zur Workspace-Konfiguration.
