"""
Configuration management for VariousPlug following SOLID principles.
"""

from pathlib import Path
from typing import Any

import click
import yaml

from .interfaces import IConfigManager


class ConfigManager(IConfigManager):
    """Configuration manager following Single Responsibility Principle."""

    CONFIG_DIR = ".vp"
    CONFIG_FILE = "config.yaml"

    def __init__(
        self, config_data: dict[str, Any] | Path | None = None, config_path: Path | None = None
    ):
        # Backward compatibility: support old constructor signature
        if isinstance(config_data, Path) or config_data is None:
            # Old API: ConfigManager(config_file) or ConfigManager()
            config_file = (
                config_data
                if config_data is not None
                else Path.cwd() / self.CONFIG_DIR / self.CONFIG_FILE
            )
            self._config_path = config_file
            self._data = {}  # Start with empty config for old API
        else:
            # New API: ConfigManager(config_data, config_path)
            self._data = config_data
            self._config_path = config_path or Path.cwd() / self.CONFIG_DIR / self.CONFIG_FILE

    @classmethod
    def load(cls, config_path: Path | None = None) -> "ConfigManager":
        """Load configuration from file."""
        if config_path is None:
            config_path = Path.cwd() / cls.CONFIG_DIR / cls.CONFIG_FILE

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\\n"
                f"Run 'vp --init' to initialize configuration."
            )

        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f) or {}
            return cls(config_data, config_path)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}") from e

    @classmethod
    def create_new(
        cls,
        project_name: str,
        vast_api_key: str | None = None,
        runpod_api_key: str | None = None,
        default_platform: str = "vast",
        data_dir: str = "data",
        base_image: str = "python:3.11-slim",
    ) -> "ConfigManager":
        """Create a new configuration."""
        config_data = {
            "project": {
                "name": project_name,
                "data_dir": data_dir,
                "base_image": base_image,
                "working_dir": "/workspace",
            },
            "platforms": {
                "default": default_platform,
                "vast": {"api_key": vast_api_key, "enabled": vast_api_key is not None},
                "runpod": {"api_key": runpod_api_key, "enabled": runpod_api_key is not None},
            },
            "docker": {"enabled": False, "build_context": ".", "dockerfile": "Dockerfile", "build_args": {}},
            "sync": {
                "exclude_patterns": [
                    ".git/",
                    ".vp/",
                    "__pycache__/",
                    "*.pyc",
                    ".DS_Store",
                    "node_modules/",
                    ".env",
                ],
                "include_patterns": ["*"],
            },
        }

        return cls(config_data)

    def save(self, config_path: Path | None = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = self._config_path

        # Create config directory if it doesn't exist
        config_path.parent.mkdir(exist_ok=True)

        try:
            with open(config_path, "w") as f:
                yaml.dump(self._data, f, default_flow_style=False, indent=2)
        except (PermissionError, FileNotFoundError, yaml.YAMLError):
            raise  # Re-raise as-is for specific file system and YAML errors
        except Exception as e:
            raise ValueError(f"Failed to save config: {e}") from e

    def get_project_config(self) -> dict[str, Any]:
        """Get project configuration."""
        return self._data.get("project", {})

    def get_platform_config(self, platform: str) -> dict[str, Any]:
        """Get platform-specific configuration."""
        platforms = self._data.get("platforms", {})
        return platforms.get(platform, {})

    def get_docker_config(self) -> dict[str, Any]:
        """Get Docker configuration."""
        return self._data.get("docker", {})

    def get_sync_config(self) -> dict[str, Any]:
        """Get file sync configuration."""
        return self._data.get("sync", {})

    def get_default_platform(self) -> str:
        """Get default platform."""
        return self._data.get("platforms", {}).get("default", "vast")

    def update_platform_config(self, platform: str, config: dict[str, Any]):
        """Update platform configuration."""
        if "platforms" not in self._data:
            self._data["platforms"] = {}
        if platform not in self._data["platforms"]:
            self._data["platforms"][platform] = {}

        self._data["platforms"][platform].update(config)

    def set_default_platform(self, platform: str):
        """Set default platform."""
        if "platforms" not in self._data:
            self._data["platforms"] = {}
        self._data["platforms"]["default"] = platform

    # Backward compatibility properties
    @property
    def config_file(self) -> Path:
        """Backward compatibility property for config file path."""
        return self._config_path

    @property
    def config(self) -> dict[str, Any]:
        """Backward compatibility property for config data."""
        return self._data

    @config.setter
    def config(self, value: dict[str, Any]):
        """Backward compatibility setter for config data."""
        self._data = value

    def create_default_config(
        self,
        project_name: str = "default",
        data_dir: str = "data",
        base_image: str = "python:3.11-slim",
    ) -> dict[str, Any]:
        """Backward compatibility method for creating default config."""
        default_config = {
            "project": {
                "name": project_name,
                "data_dir": data_dir,
                "base_image": base_image,
                "working_dir": "/workspace",
            },
            "platforms": {
                "default": "vast",
                "vast": {"api_key": None, "enabled": False},
                "runpod": {"api_key": None, "enabled": False},
            },
            "docker": {
                "build_context": ".",
                "dockerfile": "Dockerfile",
                "build_args": {},
            },
            "sync": {
                "exclude_patterns": [
                    ".git/",
                    ".vp/",
                    "__pycache__/",
                    "*.pyc",
                    ".DS_Store",
                    "node_modules/",
                    ".env",
                ],
                "include_patterns": ["*"],
            },
        }
        self._data.update(default_config)
        return default_config

    def load_from_file(self) -> dict[str, Any]:
        """Backward compatibility instance method to load config from file."""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self._config_path}\\n"
                f"Run 'vp --init' to initialize configuration."
            )

        with open(self._config_path) as f:
            config_data = yaml.safe_load(f) or {}
        self._data = config_data
        return config_data


class ConfigDisplay:
    """Separate class for displaying configuration (Single Responsibility)."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def show(self):
        """Display current configuration."""
        click.echo("Current Configuration:")
        click.echo("=" * 50)

        # Project info
        project = self.config_manager.get_project_config()
        click.echo(f"Project Name: {project.get('name', 'N/A')}")
        click.echo(f"Data Directory: {project.get('data_dir', 'N/A')}")
        click.echo(f"Base Image: {project.get('base_image', 'N/A')}")
        click.echo()

        # Platform info
        click.echo(f"Default Platform: {self.config_manager.get_default_platform()}")
        click.echo()

        # Vast.ai
        vast = self.config_manager.get_platform_config("vast")
        vast_enabled = vast.get("enabled", False)
        vast_key = vast.get("api_key", "")
        click.echo(f"Vast.ai: {'Enabled' if vast_enabled else 'Disabled'}")
        if vast_enabled and vast_key:
            click.echo(f"  API Key: {'*' * (len(vast_key) - 4) + vast_key[-4:]}")
        click.echo()

        # RunPod
        runpod = self.config_manager.get_platform_config("runpod")
        runpod_enabled = runpod.get("enabled", False)
        runpod_key = runpod.get("api_key", "")
        click.echo(f"RunPod: {'Enabled' if runpod_enabled else 'Disabled'}")
        if runpod_enabled and runpod_key:
            click.echo(f"  API Key: {'*' * (len(runpod_key) - 4) + runpod_key[-4:]}")


class ConfigFileGenerator:
    """Separate class for generating config files (Single Responsibility)."""

    @staticmethod
    def create_dockerfile(base_image: str) -> Path:
        """Create a default Dockerfile."""
        dockerfile_path = Path.cwd() / "Dockerfile"
        if dockerfile_path.exists():
            return dockerfile_path

        dockerfile_content = f"""# Generated by VariousPlug
FROM {base_image}

# Set working directory
WORKDIR /workspace

# Copy requirements if they exist
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Copy project files
COPY . .

# Default command
CMD ["python", "--version"]
"""

        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        return dockerfile_path

    @staticmethod
    def create_vpignore(exclude_patterns: list) -> Path:
        """Create a default .vpignore file."""
        vpignore_path = Path.cwd() / ".vpignore"
        if vpignore_path.exists():
            return vpignore_path

        vpignore_content = """# VariousPlug ignore file
# Similar to .gitignore, but for file synchronization

""" + "\\n".join(exclude_patterns)

        with open(vpignore_path, "w") as f:
            f.write(vpignore_content)

        return vpignore_path


# Legacy alias for backward compatibility
Config = ConfigManager
