"""
Unit tests for VariousPlug CLI commands.
"""

from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from variousplug.cli import DependencyContainer, cli
from variousplug.config import ConfigManager
from variousplug.interfaces import InstanceInfo, InstanceStatus


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "VariousPlug" in result.output
        assert "run" in result.output
        assert "list-instances" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_list_instances_command(self, mock_container_class, mock_config_load):
        """Test list-instances command."""
        # Mock configuration
        mock_config = Mock()
        mock_config.get_default_platform.return_value = "vast"
        mock_config_load.return_value = mock_config

        # Mock container
        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instances = [
            InstanceInfo(
                id="test_123", platform="vast", status=InstanceStatus.RUNNING, gpu_type="GTX_1080"
            )
        ]
        mock_instance_manager.list_instances.return_value = mock_instances
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances"])

        assert result.exit_code == 0
        assert "test_123" in result.output
        assert "vast" in result.output
        assert "running" in result.output
        assert "GTX_1080" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_list_instances_specific_platform(self, mock_container_class, mock_config_load):
        """Test list-instances command with specific platform."""
        # Mock configuration
        mock_config = Mock()
        mock_config_load.return_value = mock_config

        # Mock container
        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instances = [
            InstanceInfo(
                id="runpod_456",
                platform="runpod",
                status=InstanceStatus.PENDING,
                gpu_type="RTX_4090",
            )
        ]
        mock_instance_manager.list_instances.return_value = mock_instances
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances", "--platform", "runpod"])

        assert result.exit_code == 0
        assert "runpod_456" in result.output
        assert "runpod" in result.output
        assert "pending" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_list_instances_no_instances(self, mock_container_class, mock_config_load):
        """Test list-instances command with no instances."""
        # Mock configuration
        mock_config = Mock()
        mock_config.get_default_platform.return_value = "vast"
        mock_config_load.return_value = mock_config

        # Mock container
        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instance_manager.list_instances.return_value = []
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances"])

        assert result.exit_code == 0
        assert "No instances found" in result.output

    def test_ls_alias(self):
        """Test ls command as alias for list-instances."""
        runner = CliRunner()
        result = runner.invoke(cli, ["ls", "--help"])

        assert result.exit_code == 0
        assert "alias for list-instances" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_create_instance_command(self, mock_container_class, mock_config_load):
        """Test create-instance command."""
        # Mock configuration
        mock_config = Mock()
        mock_config_load.return_value = mock_config

        # Mock container
        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instance = InstanceInfo(
            id="new_123", platform="vast", status=InstanceStatus.PENDING, gpu_type="GTX_1080"
        )
        mock_instance_manager.create_instance.return_value = mock_instance
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create-instance",
                "--platform",
                "vast",
                "--gpu-type",
                "GTX_1080",
                "--image",
                "pytorch/pytorch",
            ],
        )

        assert result.exit_code == 0
        assert "new_123" in result.output
        assert "created successfully" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_destroy_instance_command(self, mock_container_class, mock_config_load):
        """Test destroy-instance command."""
        # Mock configuration
        mock_config = Mock()
        mock_config_load.return_value = mock_config

        # Mock container
        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instance_manager.destroy_instance.return_value = True
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["destroy-instance", "test_123", "--platform", "vast"])

        assert result.exit_code == 0
        assert "destroyed successfully" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    @patch("variousplug.cli._auto_select_instance")
    def test_run_command(self, mock_auto_select, mock_container_class, mock_config_load):
        """Test run command."""
        # Mock configuration
        mock_config = Mock()
        mock_config.get_default_platform.return_value = "vast"
        mock_config_load.return_value = mock_config

        # Mock auto-selection
        mock_auto_select.return_value = "test-instance-123"

        # Mock container
        mock_container = Mock()
        mock_workflow_executor = Mock()
        from variousplug.utils import ExecutionResult

        mock_workflow_executor.execute_workflow.return_value = ExecutionResult(
            True, "Command executed"
        )
        mock_container.workflow_executor = mock_workflow_executor
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--", "python", "--version"])

        assert result.exit_code == 0

    @patch("variousplug.cli.ConfigManager")
    def test_config_show_command(self, mock_config_manager_class):
        """Test config-show command."""
        # Mock config manager
        mock_config = Mock()
        mock_config.get_project_config.return_value = {
            "name": "test-project",
            "data_dir": "data",
            "base_image": "python:3.11",
        }
        mock_config.get_default_platform.return_value = "vast"
        mock_config.get_platform_config.return_value = {"api_key": "test_key", "enabled": True}
        mock_config_manager_class.load.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config-show"])

        assert result.exit_code == 0
        assert "test-project" in result.output
        assert "vast" in result.output

    @patch("variousplug.cli.ConfigManager")
    def test_config_set_command(self, mock_config_manager_class):
        """Test config-set command."""
        # Mock config manager
        mock_config = Mock()
        mock_config_manager_class.load.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            cli, ["config-set", "--vast-api-key", "new_vast_key", "--default-platform", "runpod"]
        )

        assert result.exit_code == 0
        assert "Configuration updated successfully" in result.output

        # Verify methods were called
        mock_config.update_platform_config.assert_called()
        mock_config.set_default_platform.assert_called_with("runpod")
        mock_config.save.assert_called()

    @patch("variousplug.cli.initialize_config")
    def test_init_flag(self, mock_initialize_config):
        """Test --init flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--init"])

        assert result.exit_code == 0
        mock_initialize_config.assert_called_once()

    def test_init_command_interactive(self):
        """Test initialize_config function."""
        with (
            patch("click.prompt") as mock_prompt,
            patch("variousplug.cli.ConfigManager") as mock_config_class,
            patch("variousplug.cli.ConfigFileGenerator") as mock_file_gen,
        ):
            # Mock user inputs
            mock_prompt.side_effect = [
                "test-project",  # project name
                "test_vast_key",  # vast api key
                "test_runpod_key",  # runpod api key
                "vast",  # default platform
                "data",  # data directory
                "python:3.11-slim",  # base image
            ]

            # Mock config manager
            mock_config = Mock()
            mock_config.get_project_config.return_value = {"base_image": "python:3.11-slim"}
            mock_config.get_sync_config.return_value = {"exclude_patterns": [".git/", ".vp/"]}
            mock_config_class.create_new.return_value = mock_config

            from variousplug.cli import initialize_config

            runner = CliRunner()
            with runner.isolated_filesystem():
                initialize_config()

            # Verify config was created and saved
            mock_config_class.create_new.assert_called_once()
            mock_config.save.assert_called_once()
            mock_file_gen.create_dockerfile.assert_called_once()
            mock_file_gen.create_vpignore.assert_called_once()


class TestDependencyContainer:
    """Test DependencyContainer class."""

    def test_dependency_container_init(self, config_manager):
        """Test DependencyContainer initialization."""
        container = DependencyContainer(config_manager, "vast")

        assert container.config_manager == config_manager
        assert container.platform == "vast"
        assert container.platform_client is not None
        assert container.file_sync is not None
        assert container.docker_builder is not None
        assert container.workflow_executor is not None
        assert container.instance_manager is not None
        assert container.factory is not None

    def test_dependency_container_different_platform(self, config_manager):
        """Test DependencyContainer with different platform."""
        container = DependencyContainer(config_manager, "runpod")

        assert container.platform == "runpod"
        assert container.platform_client is not None

    def test_dependency_container_invalid_platform(self, config_manager):
        """Test DependencyContainer with invalid platform."""
        with pytest.raises(ValueError, match="Unsupported platform"):
            DependencyContainer(config_manager, "invalid_platform")

    def test_dependency_container_missing_api_key(self, temp_dir):
        """Test DependencyContainer with missing API key."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "project": {"name": "test"},
            "platforms": {
                "vast": {"enabled": True}  # No API key
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config_manager = ConfigManager(config_file)
        config_manager.load_from_file()

        with pytest.raises(ValueError, match="API key not configured"):
            DependencyContainer(config_manager, "vast")


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @patch("variousplug.cli.ConfigManager.load")
    def test_config_load_error(self, mock_config_load):
        """Test CLI with configuration load error."""
        mock_config_load.side_effect = FileNotFoundError("Config not found")

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances"])

        assert result.exit_code == 1
        assert "Config not found" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_container_creation_error(self, mock_container_class, mock_config_load):
        """Test CLI with container creation error."""
        mock_config_load.return_value = Mock()
        mock_container_class.side_effect = ValueError("Invalid platform")

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances", "--platform", "vast"])

        assert result.exit_code == 1
        assert "Invalid platform" in result.output

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_instance_manager_error(self, mock_container_class, mock_config_load):
        """Test CLI with instance manager error."""
        mock_config_load.return_value = Mock()
        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instance_manager.list_instances.side_effect = Exception("API Error")
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances", "--platform", "vast"])

        assert result.exit_code == 1
        assert "Failed to list instances" in result.output

    @patch("variousplug.cli.ConfigManager")
    def test_config_save_error(self, mock_config_manager_class):
        """Test config-set with save error."""
        mock_config = Mock()
        mock_config.save.side_effect = Exception("Save failed")
        mock_config_manager_class.load.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config-set", "--vast-api-key", "test_key"])

        assert result.exit_code == 1
        assert "Failed to update config" in result.output


class TestCLIFlags:
    """Test CLI flags and options."""

    def test_verbose_flag(self):
        """Test --verbose flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])

        assert result.exit_code == 0

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_platform_flag(self, mock_container_class, mock_config_load):
        """Test --platform flag override."""
        mock_config = Mock()
        mock_config_load.return_value = mock_config

        mock_container = Mock()
        mock_instance_manager = Mock()
        mock_instance_manager.list_instances.return_value = []
        mock_container.instance_manager = mock_instance_manager
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(cli, ["list-instances", "--platform", "runpod"])

        assert result.exit_code == 0
        # Verify container was created with runpod platform
        mock_container_class.assert_called_with(mock_config, "runpod")

    @patch("variousplug.cli.ConfigManager.load")
    @patch("variousplug.cli.DependencyContainer")
    def test_run_command_flags(self, mock_container_class, mock_config_load):
        """Test run command with various flags."""
        mock_config = Mock()
        mock_config.get_default_platform.return_value = "vast"
        mock_config_load.return_value = mock_config

        mock_container = Mock()
        mock_workflow_executor = Mock()
        from variousplug.utils import ExecutionResult

        mock_workflow_executor.execute_workflow.return_value = ExecutionResult(
            True, "Command executed"
        )
        mock_container.workflow_executor = mock_workflow_executor
        mock_container_class.return_value = mock_container

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--platform",
                "vast",
                "--instance-id",
                "test_123",
                "--no-sync",
                "run",
                "--",
                "python",
                "script.py",
            ],
        )

        assert result.exit_code == 0
        mock_workflow_executor.execute_workflow.assert_called_once()

        # Check the call arguments
        call_args = mock_workflow_executor.execute_workflow.call_args
        assert call_args[1]["instance_id"] == "test_123"
        assert call_args[1]["no_sync"] is True
