"""
Utility functions for VariousPlug.
"""
import fnmatch
import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False)]
    )


def print_success(message: str):
    """Print a success message."""
    console.print(f"✅ {message}", style="green")


def print_error(message: str):
    """Print an error message."""
    console.print(f"❌ {message}", style="red")


def print_info(message: str):
    """Print an info message."""
    console.print(f"ℹ️  {message}", style="blue")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"⚠️  {message}", style="yellow")


class ExecutionResult:
    """Result of command execution."""

    def __init__(self, success: bool, output: str | None = None,
                 error: str | None = None, exit_code: int = 0):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code


def should_exclude_file(file_path: Path, exclude_patterns: list[str],
                       include_patterns: list[str]) -> bool:
    """Check if a file should be excluded from sync."""
    file_str = str(file_path)

    # Check include patterns first
    included = False
    for pattern in include_patterns:
        if fnmatch.fnmatch(file_str, pattern):
            included = True
            break

    if not included:
        return True

    # Check exclude patterns
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_str, pattern):
            return True
        # Also check directory patterns
        if file_path.is_dir() and fnmatch.fnmatch(file_str + "/", pattern):
            return True

    return False


def get_sync_files(base_path: Path, exclude_patterns: list[str],
                  include_patterns: list[str]) -> list[Path]:
    """Get list of files to sync."""
    files = []

    for item in base_path.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(base_path)
            if not should_exclude_file(rel_path, exclude_patterns, include_patterns):
                files.append(rel_path)

    return files


def validate_command(command: list[str]) -> bool:
    """Validate that command is not empty and safe."""
    if not command:
        return False

    # Basic safety check - don't allow certain dangerous commands
    dangerous_commands = ["rm", "rmdir", "del", "format", "fdisk"]
    if command[0].lower() in dangerous_commands:
        return False

    return True


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


