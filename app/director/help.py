"""
Director-lite help system.

Provides comprehensive help for director commands.
"""

from typing import Dict, List


class DirectorHelp:
    """Provides help for director commands."""
    
    COMMANDS = {
        "status": {
            "description": "Show current pipeline status",
            "usage": "python -m app director status --project-root <path> --episode <id> --shot <id> [--json]",
            "parameters": [
                "--project-root: Path to project root",
                "--episode: Episode ID",
                "--shot: Shot ID",
                "--json: Output as JSON"
            ],
            "output": "Current state, expected next action, available actions, artifact path, known limitations"
        },
        "validate": {
            "description": "Validate RC artifacts",
            "usage": "python -m app director validate --project-root <path> --episode <id> --shot <id> [--json]",
            "parameters": [
                "--project-root: Path to project root",
                "--episode: Episode ID",
                "--shot: Shot ID",
                "--json: Output as JSON"
            ],
            "output": "Validation status, passed checks, warnings, errors, artifact index status, terminal state status"
        },
        "inspect": {
            "description": "Inspect artifact paths",
            "usage": "python -m app director inspect --project-root <path> --episode <id> --shot <id> [--json]",
            "parameters": [
                "--project-root: Path to project root",
                "--episode: Episode ID",
                "--shot: Shot ID",
                "--json: Output as JSON"
            ],
            "output": "Paths to all artifacts: project_profile, prompt_pack, submitted_workflow, observed_settings, frames_manifest, generated frame, qc_report, scene.mp4, scene_manifest, qa_report, audio_manifest, final_manifest, ledger, artifact_index"
        },
        "history": {
            "description": "Show pipeline event history from ledger",
            "usage": "python -m app director history --project-root <path> --episode <id> --shot <id> [--json]",
            "parameters": [
                "--project-root: Path to project root",
                "--episode: Episode ID",
                "--shot: Shot ID",
                "--json: Output as JSON"
            ],
            "output": "Ordered events from ledger: generate_frames, QC, assemble_scene, qa_review, attach_audio/no-audio policy, render_episode/final manifest, state transitions"
        },
        "help": {
            "description": "Show help for director commands",
            "usage": "python -m app director help [command]",
            "parameters": [
                "[command]: Optional command name for specific help"
            ],
            "output": "Available commands, their usage, and parameters"
        }
    }
    
    @classmethod
    def get_command_help(cls, command: str) -> Dict:
        """Get help for a specific command.
        
        Args:
            command: Command name
            
        Returns:
            Help dictionary for the command
        """
        return cls.COMMANDS.get(command, {})
    
    @classmethod
    def list_commands(cls) -> List[str]:
        """List all available commands.
        
        Returns:
            List of command names
        """
        return list(cls.COMMANDS.keys())
    
    @classmethod
    def get_all_help(cls) -> Dict[str, Dict]:
        """Get help for all commands.
        
        Returns:
            Dictionary mapping command names to help
        """
        return cls.COMMANDS
    
    @classmethod
    def format_command_help(cls, command: str) -> str:
        """Format help for a command as text.
        
        Args:
            command: Command name
            
        Returns:
            Formatted help text
        """
        help_data = cls.get_command_help(command)
        if not help_data:
            return f"Unknown command: {command}"
        
        lines = [
            f"Command: {command}",
            f"Description: {help_data.get('description', 'N/A')}",
            f"Usage: {help_data.get('usage', 'N/A')}",
            "",
            "Parameters:"
        ]
        
        for param in help_data.get('parameters', []):
            lines.append(f"  {param}")
        
        lines.append("")
        lines.append(f"Output: {help_data.get('output', 'N/A')}")
        
        return "\n".join(lines)
    
    @classmethod
    def format_overview(cls) -> str:
        """Format overview of all commands as text.
        
        Returns:
            Formatted overview text
        """
        lines = [
            "Director-lite Commands",
            "",
            "Director-lite provides read-only inspection of frozen RC proof packs.",
            "These commands do not mutate artifacts or execute pipeline actions.",
            "",
            "Available Commands:"
        ]
        
        for cmd in cls.list_commands():
            help_data = cls.get_command_help(cmd)
            lines.append(f"  {cmd}: {help_data.get('description', 'N/A')}")
        
        lines.append("")
        lines.append("Use 'python -m app director help <command>' for detailed help on a specific command.")
        lines.append("")
        lines.append("All commands support --json flag for structured JSON output.")
        lines.append("")
        lines.append("Example:")
        lines.append("  python -m app director status --project-root /path/to/project --episode ep01 --shot shot01 --json")
        
        return "\n".join(lines)
