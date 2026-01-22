#!/usr/bin/env python3
"""
Valtheron CLI - Command Line Interface for the Agentic Workspace.
Provides commands for managing agents, executing tasks, and running workflows.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.DIM = ''
        cls.RESET = ''


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


def print_json(data: dict, indent: int = 2):
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


class ValtheroCLI:
    """Main CLI application class."""
    
    def __init__(self):
        self.workspace_dir = Path.cwd()
        self.config = None
        self.orchestrator = None
        self.provider = None
    
    def load_config(self) -> bool:
        """Load workspace configuration."""
        config_path = self.workspace_dir / "config" / "workspace.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    self.config = json.load(f)
                return True
            except Exception as e:
                print_error(f"Failed to load config: {e}")
        return False
    
    def init_orchestrator(self):
        """Initialize the agent orchestrator."""
        if self.orchestrator is not None:
            return
        
        try:
            from utils.agent_orchestrator import AgentOrchestrator
            
            agents_path = str(self.workspace_dir / "agents")
            self.orchestrator = AgentOrchestrator(config_dir=agents_path)
            self.orchestrator.load_agents()
        except ImportError as e:
            print_warning(f"Could not initialize orchestrator: {e}")
        except Exception as e:
            print_warning(f"Orchestrator initialization error: {e}")
    
    def init_provider(self):
        """Initialize the LLM provider."""
        if self.provider is not None:
            return True
        
        try:
            from providers.anthropic_provider import create_claude_client
            
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.provider = create_claude_client(api_key=api_key)
                return True
            else:
                print_warning("ANTHROPIC_API_KEY not set. LLM features unavailable.")
        except ImportError as e:
            print_warning(f"Could not initialize provider: {e}")
        
        return False
    
    # ==================== Commands ====================
    
    def cmd_init(self, args):
        """Initialize a new Valtheron workspace."""
        print_header("Initializing Valtheron Workspace")
        
        target_dir = Path(args.directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        dirs = ["agents", "config", "tools", "workflows", "logs", "utils"]
        for d in dirs:
            (target_dir / d).mkdir(exist_ok=True)
            print_success(f"Created directory: {d}/")
        
        # Create default workspace config
        workspace_config = {
            "workspace": {
                "name": args.name or target_dir.name,
                "version": "1.0.0",
                "description": "Valtheron Agentic Workspace"
            },
            "paths": {
                "agents": "./agents",
                "tools": "./tools",
                "workflows": "./workflows",
                "logs": "./logs"
            },
            "execution": {
                "parallel": True,
                "parallel_max_workers": 4,
                "timeout_seconds": 300
            },
            "security": {
                "validate_inputs": True,
                "sanitize_outputs": True
            }
        }
        
        config_path = target_dir / "config" / "workspace.json"
        with open(config_path, 'w') as f:
            json.dump(workspace_config, f, indent=2)
        print_success(f"Created workspace configuration")
        
        print(f"\n{Colors.GREEN}Workspace initialized successfully!{Colors.RESET}")
        print(f"\nNext steps:")
        print(f"  1. cd {target_dir}")
        print(f"  2. Set ANTHROPIC_API_KEY environment variable")
        print(f"  3. Run: valtheron agent list")
    
    def cmd_agent_list(self, args):
        """List all registered agents."""
        print_header("Registered Agents")
        
        # Show agents from config files directly
        agents_dir = self.workspace_dir / "agents"
        if not agents_dir.exists():
            print_info("No agents directory found.")
            return
        
        found = False
        for f in agents_dir.glob("*.json"):
            try:
                with open(f) as file:
                    agent = json.load(file)
                found = True
                print(f"{Colors.BOLD}{agent.get('name', f.stem)}{Colors.RESET}")
                print(f"  Type: {agent.get('type', 'N/A')}")
                model_info = agent.get('model', {})
                if isinstance(model_info, dict):
                    print(f"  Model: {model_info.get('name', 'N/A')}")
                else:
                    print(f"  Model: {model_info}")
                caps = agent.get('capabilities', [])
                if caps:
                    print(f"  Capabilities: {', '.join(caps)}")
                print()
            except Exception as e:
                continue
        
        if not found:
            print_info("No agent configurations found in ./agents/")
            print_info("Create agent JSON files in the agents/ directory.")
    
    def cmd_agent_run(self, args):
        """Run a task with a specific agent."""
        print_header(f"Running Task: {args.task}")
        
        # Parse parameters
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                # Try key=value format
                for p in args.params.split(','):
                    if '=' in p:
                        k, v = p.split('=', 1)
                        params[k.strip()] = v.strip()
        
        print_info(f"Agent: {args.agent or 'auto-select'}")
        print_info(f"Action: {args.task}")
        print_info(f"Parameters: {params}")
        print()
        
        # Try to use orchestrator
        self.init_orchestrator()
        
        if self.orchestrator:
            try:
                result = self.orchestrator.execute_task(
                    name=args.task,
                    action=args.task,
                    params=params,
                    agent_name=args.agent
                )
                
                if result.status == "completed":
                    print_success("Task completed successfully!")
                    print(f"\n{Colors.DIM}Result:{Colors.RESET}")
                    print_json(result.result if result.result else {})
                else:
                    print_error(f"Task failed: {result.error}")
                    return 1
            except Exception as e:
                print_error(f"Task execution error: {e}")
                return 1
        else:
            print_warning("Orchestrator not available. Simulating task execution.")
            print_info("Task would be executed with the specified parameters.")
        
        return 0
    
    def cmd_chat(self, args):
        """Start an interactive chat with Claude."""
        print_header("Chat with Claude")
        
        if not self.init_provider():
            print_error("LLM provider not available. Set ANTHROPIC_API_KEY.")
            return 1
        
        system_prompt = args.system or (
            "You are a helpful AI assistant working within the Valtheron "
            "agentic workspace. You can help with code analysis, task planning, "
            "and general questions."
        )
        
        print_info(f"Model: {self.provider.config.model}")
        print_info("Type 'exit' or 'quit' to end the conversation.\n")
        
        messages = []
        
        while True:
            try:
                user_input = input(f"{Colors.CYAN}You:{Colors.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ('exit', 'quit', 'q'):
                print_info("Goodbye!")
                break
            
            try:
                from providers.base_provider import LLMMessage
                
                if not messages:
                    messages.append(LLMMessage.system(system_prompt))
                
                messages.append(LLMMessage.user(user_input))
                
                print(f"\n{Colors.GREEN}Claude:{Colors.RESET} ", end="", flush=True)
                
                if args.stream:
                    # Stream response
                    full_response = ""
                    for chunk in self.provider.stream(messages):
                        print(chunk, end="", flush=True)
                        full_response += chunk
                    print("\n")
                    messages.append(LLMMessage.assistant(full_response))
                else:
                    # Regular response
                    response = self.provider.complete(messages)
                    print(response.content)
                    print()
                    messages.append(LLMMessage.assistant(response.content))
                
            except Exception as e:
                print_error(f"Error: {e}")
        
        return 0
    
    def cmd_workflow_list(self, args):
        """List available workflows."""
        print_header("Available Workflows")
        
        workflows_dir = self.workspace_dir / "workflows"
        if not workflows_dir.exists():
            print_info("No workflows directory found.")
            return
        
        found = False
        for f in workflows_dir.glob("*.json"):
            try:
                with open(f) as file:
                    wf = json.load(file)
                found = True
                print(f"{Colors.BOLD}{wf.get('name', f.stem)}{Colors.RESET}")
                print(f"  Version: {wf.get('version', 'N/A')}")
                print(f"  Steps: {len(wf.get('steps', []))}")
                desc = wf.get('description', 'No description')
                print(f"  Description: {desc[:60]}{'...' if len(desc) > 60 else ''}")
                print()
            except Exception:
                continue
        
        for f in workflows_dir.glob("*.yaml"):
            try:
                import yaml
                with open(f) as file:
                    wf = yaml.safe_load(file)
                found = True
                print(f"{Colors.BOLD}{wf.get('name', f.stem)}{Colors.RESET}")
                print(f"  Version: {wf.get('version', 'N/A')}")
                print(f"  Steps: {len(wf.get('steps', []))}")
                print()
            except Exception:
                continue
        
        if not found:
            print_info("No workflows found in ./workflows/")
    
    def cmd_workflow_run(self, args):
        """Execute a workflow."""
        print_header(f"Running Workflow: {args.workflow}")
        
        # Find workflow file
        workflows_dir = self.workspace_dir / "workflows"
        workflow_path = None
        
        for ext in ['.json', '.yaml', '.yml']:
            candidate = workflows_dir / f"{args.workflow}{ext}"
            if candidate.exists():
                workflow_path = candidate
                break
        
        if not workflow_path:
            print_error(f"Workflow not found: {args.workflow}")
            return 1
        
        # Load workflow
        try:
            with open(workflow_path) as f:
                if workflow_path.suffix in ['.yaml', '.yml']:
                    import yaml
                    workflow = yaml.safe_load(f)
                else:
                    workflow = json.load(f)
        except Exception as e:
            print_error(f"Failed to load workflow: {e}")
            return 1
        
        # Parse inputs
        inputs = {}
        if args.inputs:
            try:
                inputs = json.loads(args.inputs)
            except json.JSONDecodeError:
                print_error("Invalid JSON for inputs")
                return 1
        
        print_info(f"Workflow: {workflow.get('name')}")
        print_info(f"Steps: {len(workflow.get('steps', []))}")
        print()
        
        # Execute
        try:
            from utils.workflow_engine import WorkflowEngine
            
            engine = WorkflowEngine()
            result = engine.execute(workflow, inputs, parallel=args.parallel)
            
            print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
            print(f"  Status: ", end="")
            if result.status.value == "completed":
                print_success("Completed")
            else:
                print_error(result.status.value)
            print(f"  Duration: {result.duration_ms:.2f}ms")
            print(f"  Success Rate: {result.success_rate:.1f}%")
            
            if args.verbose:
                print(f"\n{Colors.DIM}Step Details:{Colors.RESET}")
                for name, step in result.steps.items():
                    status_icon = "✓" if step.status.value == "completed" else "✗"
                    print(f"  {status_icon} {name}: {step.status.value}")
            
        except ImportError as e:
            print_error(f"Workflow engine not available: {e}")
            return 1
        except Exception as e:
            print_error(f"Workflow execution failed: {e}")
            return 1
        
        return 0
    
    def cmd_tool_list(self, args):
        """List available tools."""
        print_header("Available Tools")
        
        # List tool definition files
        tools_dir = self.workspace_dir / "tools"
        
        # Check for definitions
        definitions_dir = tools_dir / "definitions"
        if definitions_dir.exists():
            for f in definitions_dir.glob("*.json"):
                try:
                    with open(f) as file:
                        tool = json.load(file)
                    print(f"{Colors.BOLD}{tool['name']}{Colors.RESET}")
                    print(f"  {tool.get('description', 'No description')[:70]}")
                    print()
                except Exception:
                    continue
        
        # Also list built-in tools
        print(f"{Colors.BOLD}Built-in Tools:{Colors.RESET}")
        builtin_tools = [
            ("code_analyzer", "Analyzes code for complexity, security, and performance"),
            ("test_runner", "Executes tests using pytest or jest"),
            ("read", "Read file contents"),
            ("write", "Write content to files"),
            ("glob", "Search for files matching patterns"),
            ("grep", "Search file contents for patterns"),
            ("edit", "Edit files with search and replace"),
        ]
        for name, desc in builtin_tools:
            print(f"  • {name}: {desc}")
    
    def cmd_analyze(self, args):
        """Analyze code using the code analyzer tool."""
        print_header(f"Analyzing: {args.file}")
        
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            return 1
        
        # Detect language from extension
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust'
        }
        language = args.language or lang_map.get(file_path.suffix, 'python')
        
        try:
            # Try to import the code analyzer
            from tools.implementations.code_analyzer import CodeAnalyzerTool
            
            analyzer = CodeAnalyzerTool()
            result = analyzer(
                file_path=str(file_path),
                language=language,
                analysis_type=args.type
            )
            
            if result.is_success:
                data = result.data
                
                print(f"{Colors.BOLD}Quality Score: {data['metrics']['quality_score']}/100{Colors.RESET}")
                print(f"Cyclomatic Complexity: {data['metrics']['cyclomatic_complexity']}")
                
                loc = data['metrics'].get('loc', {})
                print(f"Lines of Code: {loc.get('code_lines', 'N/A')}")
                print(f"Comment Ratio: {loc.get('comment_ratio', 0):.1f}%")
                
                if data['issues']:
                    print(f"\n{Colors.BOLD}Issues Found ({len(data['issues'])}):{Colors.RESET}")
                    for issue in data['issues'][:10]:
                        severity_colors = {
                            'critical': Colors.RED,
                            'high': Colors.RED,
                            'medium': Colors.YELLOW,
                            'low': Colors.DIM
                        }
                        color = severity_colors.get(issue['severity'], '')
                        line_info = f" (line {issue['line']})" if issue.get('line') else ""
                        print(f"  {color}[{issue['severity'].upper()}]{Colors.RESET} {issue['message']}{line_info}")
                
                if data['recommendations']:
                    print(f"\n{Colors.BOLD}Recommendations:{Colors.RESET}")
                    for rec in data['recommendations']:
                        print(f"  • {rec}")
            else:
                print_error(f"Analysis failed: {result.error}")
                return 1
                
        except ImportError as e:
            # Fallback: Basic analysis without the tool
            print_warning(f"Full analyzer not available: {e}")
            print_info("Performing basic analysis...")
            
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                total_lines = len(lines)
                blank_lines = sum(1 for line in lines if not line.strip())
                comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*')))
                code_lines = total_lines - blank_lines - comment_lines
                
                print(f"\n{Colors.BOLD}Basic Metrics:{Colors.RESET}")
                print(f"  Total Lines: {total_lines}")
                print(f"  Code Lines: {code_lines}")
                print(f"  Blank Lines: {blank_lines}")
                print(f"  Comment Lines: {comment_lines}")
                
                if code_lines > 0:
                    comment_ratio = (comment_lines / code_lines) * 100
                    print(f"  Comment Ratio: {comment_ratio:.1f}%")
                
            except Exception as e:
                print_error(f"Could not read file: {e}")
                return 1
        
        return 0
    
    def cmd_version(self, args):
        """Show version information."""
        print(f"{Colors.BOLD}Valtheron{Colors.RESET} v1.0.0")
        print("Agentic Workspace Framework")
        print()
        print("Components:")
        
        # Check available components
        components = [
            ("Agent Orchestrator", "utils.agent_orchestrator"),
            ("Workflow Engine", "utils.workflow_engine"),
            ("Tool System", "tools.implementations"),
            ("Anthropic Provider", "providers.anthropic_provider"),
        ]
        
        for name, module in components:
            try:
                __import__(module)
                print(f"  {Colors.GREEN}✓{Colors.RESET} {name}")
            except ImportError:
                print(f"  {Colors.RED}✗{Colors.RESET} {name}")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='valtheron',
        description='Valtheron - Agentic Workspace CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize a new workspace')
    init_parser.add_argument('directory', nargs='?', default='.', help='Target directory')
    init_parser.add_argument('--name', '-n', help='Workspace name')
    
    # agent commands
    agent_parser = subparsers.add_parser('agent', help='Agent management')
    agent_sub = agent_parser.add_subparsers(dest='agent_command')
    
    agent_list = agent_sub.add_parser('list', help='List agents')
    
    agent_run = agent_sub.add_parser('run', help='Run a task with an agent')
    agent_run.add_argument('task', help='Task/action to execute')
    agent_run.add_argument('--agent', '-a', help='Specific agent to use')
    agent_run.add_argument('--params', '-p', help='Parameters (JSON or key=value)')
    
    # chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat with Claude')
    chat_parser.add_argument('--system', '-s', help='System prompt')
    chat_parser.add_argument('--stream', action='store_true', help='Stream responses')
    
    # workflow commands
    wf_parser = subparsers.add_parser('workflow', help='Workflow management')
    wf_sub = wf_parser.add_subparsers(dest='workflow_command')
    
    wf_list = wf_sub.add_parser('list', help='List workflows')
    
    wf_run = wf_sub.add_parser('run', help='Run a workflow')
    wf_run.add_argument('workflow', help='Workflow name')
    wf_run.add_argument('--inputs', '-i', help='Input parameters (JSON)')
    wf_run.add_argument('--parallel', action='store_true', help='Enable parallel execution')
    wf_run.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # tool commands
    tool_parser = subparsers.add_parser('tool', help='Tool management')
    tool_sub = tool_parser.add_subparsers(dest='tool_command')
    
    tool_list = tool_sub.add_parser('list', help='List tools')
    
    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code')
    analyze_parser.add_argument('file', help='File to analyze')
    analyze_parser.add_argument('--language', '-l', help='Programming language')
    analyze_parser.add_argument('--type', '-t', default='all',
                               choices=['all', 'complexity', 'security', 'performance'],
                               help='Analysis type')
    
    # version command
    version_parser = subparsers.add_parser('version', help='Show version')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()
    
    cli = ValtheroCLI()
    
    # Route to command handler
    if args.command == 'init':
        return cli.cmd_init(args)
    elif args.command == 'agent':
        if args.agent_command == 'list':
            return cli.cmd_agent_list(args)
        elif args.agent_command == 'run':
            return cli.cmd_agent_run(args)
        else:
            parser.parse_args(['agent', '--help'])
    elif args.command == 'chat':
        return cli.cmd_chat(args)
    elif args.command == 'workflow':
        if args.workflow_command == 'list':
            return cli.cmd_workflow_list(args)
        elif args.workflow_command == 'run':
            return cli.cmd_workflow_run(args)
        else:
            parser.parse_args(['workflow', '--help'])
    elif args.command == 'tool':
        if args.tool_command == 'list':
            return cli.cmd_tool_list(args)
        else:
            parser.parse_args(['tool', '--help'])
    elif args.command == 'analyze':
        return cli.cmd_analyze(args)
    elif args.command == 'version':
        return cli.cmd_version(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
