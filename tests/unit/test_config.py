"""
Unit tests for VariousPlug configuration management.
"""
from unittest.mock import mock_open, patch

import pytest
import yaml

from variousplug.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager class."""

    def test_init_with_config_file(self, temp_dir):
        """Test ConfigManager initialization with config file."""
        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)

        assert manager.config_file == config_file
        assert manager.config == {}

    def test_init_default_config_file(self, temp_dir, monkeypatch):
        """Test ConfigManager initialization with default config file."""
        monkeypatch.chdir(temp_dir)
        manager = ConfigManager()

        expected_path = temp_dir / ".vp" / "config.yaml"
        assert manager.config_file == expected_path

    def test_load_existing_config(self, temp_dir, sample_config):
        """Test loading existing configuration."""
        config_file = temp_dir / "config.yaml"

        # Write config to file
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        manager = ConfigManager(config_file)
        loaded_config = manager.load()

        assert loaded_config == sample_config
        assert manager.config == sample_config

    def test_load_nonexistent_config(self, temp_dir):
        """Test loading non-existent configuration."""
        config_file = temp_dir / "nonexistent.yaml"
        manager = ConfigManager(config_file)

        with pytest.raises(FileNotFoundError):
            manager.load()

    def test_save_config(self, temp_dir, sample_config):
        """Test saving configuration."""
        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)
        manager.config = sample_config

        # Ensure parent directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)

        manager.save()

        # Verify file was created and content is correct
        assert config_file.exists()

        with open(config_file) as f:
            saved_config = yaml.safe_load(f)

        assert saved_config == sample_config

    def test_save_creates_directory(self, temp_dir, sample_config):
        """Test saving configuration creates parent directory."""
        config_file = temp_dir / "new_dir" / "config.yaml"
        manager = ConfigManager(config_file)
        manager.config = sample_config

        manager.save()

        assert config_file.parent.exists()
        assert config_file.exists()

    def test_get_platform_config_existing(self, config_manager):
        """Test getting existing platform configuration."""
        vast_config = config_manager.get_platform_config("vast")

        assert vast_config == {
            "api_key": "test_vast_key",
            "enabled": True
        }

    def test_get_platform_config_nonexistent(self, config_manager):
        """Test getting non-existent platform configuration."""
        unknown_config = config_manager.get_platform_config("unknown")

        assert unknown_config == {}

    def test_update_platform_config_existing(self, config_manager):
        """Test updating existing platform configuration."""
        new_config = {
            "api_key": "new_vast_key",
            "enabled": False,
            "region": "us-east"
        }

        config_manager.update_platform_config("vast", new_config)

        updated_config = config_manager.get_platform_config("vast")
        assert updated_config == new_config

    def test_update_platform_config_new(self, config_manager):
        """Test updating configuration for new platform."""
        new_config = {
            "api_key": "aws_key",
            "enabled": True
        }

        config_manager.update_platform_config("aws", new_config)

        aws_config = config_manager.get_platform_config("aws")
        assert aws_config == new_config

    def test_get_default_platform(self, config_manager):
        """Test getting default platform."""
        default = config_manager.get_default_platform()
        assert default == "vast"

    def test_get_default_platform_missing(self, temp_dir):
        """Test getting default platform when not set."""
        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)
        manager.config = {"platforms": {}}

        default = manager.get_default_platform()
        assert default == "vast"  # Should return default fallback

    def test_set_default_platform(self, config_manager):
        """Test setting default platform."""
        config_manager.set_default_platform("runpod")

        default = config_manager.get_default_platform()
        assert default == "runpod"

    def test_set_default_platform_no_platforms_section(self, temp_dir):
        """Test setting default platform when platforms section doesn't exist."""
        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)
        manager.config = {}

        manager.set_default_platform("runpod")

        assert manager.config["platforms"]["default"] == "runpod"

    def test_create_default_config(self, temp_dir):
        """Test creating default configuration."""
        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)

        default_config = manager.create_default_config(
            project_name="test-project",
            data_dir="data",
            base_image="python:3.11-slim"
        )

        expected_config = {
            "project": {
                "name": "test-project",
                "data_dir": "data",
                "base_image": "python:3.11-slim",
                "working_dir": "/workspace"
            },
            "platforms": {
                "default": "vast",
                "vast": {
                    "api_key": None,
                    "enabled": False
                },
                "runpod": {
                    "api_key": None,
                    "enabled": False
                }
            },
            "docker": {
                "build_context": ".",
                "dockerfile": "Dockerfile",
                "build_args": {}
            },
            "sync": {
                "exclude_patterns": [
                    ".git/", ".vp/", "__pycache__/", "*.pyc",
                    ".DS_Store", "node_modules/", ".env"
                ],
                "include_patterns": ["*"]
            }
        }

        assert default_config == expected_config
        assert manager.config == expected_config

    def test_load_class_method(self, temp_dir, sample_config, monkeypatch):
        """Test ConfigManager.load() class method."""
        config_file = temp_dir / ".vp" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        monkeypatch.chdir(temp_dir)

        manager = ConfigManager.load()

        assert manager.config == sample_config
        assert manager.config_file == config_file

    def test_load_class_method_nonexistent(self, temp_dir, monkeypatch):
        """Test ConfigManager.load() class method with non-existent config."""
        monkeypatch.chdir(temp_dir)

        with pytest.raises(FileNotFoundError):
            ConfigManager.load()

    def test_get_project_config(self, config_manager):
        """Test getting project configuration."""
        project_config = config_manager.get_project_config()

        expected = {
            "name": "test-project",
            "data_dir": "data",
            "base_image": "python:3.11-slim",
            "working_dir": "/workspace"
        }

        assert project_config == expected

    def test_get_docker_config(self, config_manager):
        """Test getting Docker configuration."""
        docker_config = config_manager.get_docker_config()

        expected = {
            "build_context": ".",
            "dockerfile": "Dockerfile",
            "build_args": {}
        }

        assert docker_config == expected

    def test_get_sync_config(self, config_manager):
        """Test getting sync configuration."""
        sync_config = config_manager.get_sync_config()

        expected = {
            "exclude_patterns": [".git/", ".vp/", "*.pyc"],
            "include_patterns": ["*"]
        }

        assert sync_config == expected

    def test_yaml_error_handling(self, temp_dir):
        """Test handling of invalid YAML files."""
        config_file = temp_dir / "config.yaml"

        # Write invalid YAML
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [unclosed")

        manager = ConfigManager(config_file)

        with pytest.raises(yaml.YAMLError):
            manager.load()

    def test_save_file_permissions_error(self, temp_dir, sample_config):
        """Test save with file permissions error."""
        config_file = temp_dir / "readonly" / "config.yaml"
        config_file.parent.mkdir()
        config_file.parent.chmod(0o444)  # Read-only directory

        manager = ConfigManager(config_file)
        manager.config = sample_config

        with pytest.raises(PermissionError):
            manager.save()

        # Cleanup
        config_file.parent.chmod(0o755)

    @patch("builtins.open", mock_open())
    @patch("yaml.dump")
    def test_save_yaml_error(self, mock_yaml_dump, temp_dir, sample_config):
        """Test save with YAML dump error."""
        mock_yaml_dump.side_effect = yaml.YAMLError("YAML error")

        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)
        manager.config = sample_config

        with pytest.raises(yaml.YAMLError):
            manager.save()

    def test_config_validation(self, config_manager):
        """Test configuration validation."""
        # This would be expanded with actual validation logic
        # For now, just test that the config loads without errors
        assert config_manager.config is not None
        assert "project" in config_manager.config
        assert "platforms" in config_manager.config

    def test_merge_configs(self, temp_dir):
        """Test merging configurations (if such functionality exists)."""
        # This is a placeholder for future config merging functionality
        config_file = temp_dir / "config.yaml"
        manager = ConfigManager(config_file)

        base_config = {
            "project": {"name": "base"},
            "platforms": {"vast": {"enabled": True}}
        }

        override_config = {
            "project": {"version": "1.0"},
            "platforms": {"vast": {"api_key": "new_key"}}
        }

        # For now, just test that we can handle nested dictionaries
        manager.config = base_config
        manager.update_platform_config("vast", override_config["platforms"]["vast"])

        final_config = manager.get_platform_config("vast")
        assert final_config["enabled"] is True
        assert final_config["api_key"] == "new_key"
