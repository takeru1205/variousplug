"""
Utility functions for VariousPlug.
"""

import fnmatch
import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

console = Console()
error_console = Console(stderr=True)


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False)],
    )


def print_success(message: str):
    """Print a success message."""
    console.print(f"✅ {message}", style="green")


def print_error(message: str):
    """Print an error message."""
    error_console.print(f"❌ {message}", style="red")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[info]i[/info]  {message}", style="blue")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"⚠️  {message}", style="yellow")


class ExecutionResult:
    """Result of command execution."""

    def __init__(
        self,
        success: bool,
        output: str | None = "",
        error: str | None = "",
        exit_code: int | None = 0,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code

    def __bool__(self) -> bool:
        """Return success status as boolean."""
        return self.success

    def __str__(self) -> str:
        """String representation."""
        return f"ExecutionResult(success={self.success}, output='{self.output}', error='{self.error}', exit_code={self.exit_code})"

    def __repr__(self) -> str:
        """Repr representation."""
        return f"ExecutionResult(success={self.success}, output='{self.output}', error='{self.error}', exit_code={self.exit_code})"

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, ExecutionResult):
            return False
        return (
            self.success == other.success
            and self.output == other.output
            and self.error == other.error
            and self.exit_code == other.exit_code
        )


def should_exclude_file(
    file_path: Path, exclude_patterns: list[str], include_patterns: list[str]
) -> bool:
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


def get_sync_files(
    base_path: Path, exclude_patterns: list[str], include_patterns: list[str]
) -> list[Path]:
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
    return command[0].lower() not in dangerous_commands


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


def read_vpignore_patterns(base_path: Path | None = None) -> list[str]:
    """Read exclude patterns from .vpignore file."""
    if base_path is None:
        base_path = Path.cwd()

    vpignore_path = base_path / ".vpignore"
    patterns = []

    if vpignore_path.exists():
        try:
            with open(vpignore_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception as e:
            # Log error but don't fail the sync
            print_warning(f"Failed to read .vpignore file: {e}")

    return patterns


def merge_exclude_patterns(config_patterns: list[str], vpignore_patterns: list[str]) -> list[str]:
    """Merge exclude patterns from config and .vpignore file, removing duplicates."""
    # Use a set to avoid duplicates, then convert back to list
    all_patterns = set(config_patterns)
    all_patterns.update(vpignore_patterns)
    return list(all_patterns)
