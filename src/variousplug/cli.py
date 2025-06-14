"""
Main CLI interface for VariousPlug following SOLID principles.
"""

import sys
from pathlib import Path

import click

from .base import DockerBuilder
from .config import ConfigDisplay, ConfigFileGenerator, ConfigManager
from .executor import InstanceManager, WorkflowExecutor
from .factory import PlatformFactory
from .interfaces import InstanceStatus
from .utils import print_error, print_info, print_success, setup_logging


def _auto_select_instance(config_manager: ConfigManager, platform: str) -> str | None:
    """Auto-select the best available instance for execution."""
    try:
        factory = PlatformFactory()
        platform_config = config_manager.get_platform_config(platform)
        platform_client = factory.create_client(platform, platform_config)

        instances = platform_client.list_instances()

        # Priority: running instances first, then pending/starting
        running_instances = [i for i in instances if i.status == InstanceStatus.RUNNING]
        if running_instances:
            selected = running_instances[0]
            print_info(f"Auto-selected running instance: {selected.id} ({platform})")
            return selected.id

        available_instances = [
            i for i in instances if i.status in [InstanceStatus.PENDING, InstanceStatus.STARTING]
        ]
        if available_instances:
            selected = available_instances[0]
            print_info(f"Auto-selected pending instance: {selected.id} ({platform})")
            return selected.id

        # No instances available - could auto-create one here in the future
        print_info(f"No instances available on {platform}")
        return None

    except Exception as e:
        print_error(f"Failed to auto-select instance: {e}")
        return None


class DependencyContainer:
    """Simple dependency injection container following Dependency Inversion Principle."""

    def __init__(self, config_manager: ConfigManager, platform: str):
        self.config_manager = config_manager
        self.platform = platform
        self.factory = PlatformFactory()

        # Create platform-specific dependencies
        platform_config = config_manager.get_platform_config(platform)
        self.platform_client = self.factory.create_client(platform, platform_config)
        self.file_sync = self.factory.create_file_sync(platform, platform_config)
        self.docker_builder = DockerBuilder()

        # Create high-level services
        self.workflow_executor = WorkflowExecutor(
            config_manager, self.platform_client, self.file_sync, self.docker_builder
        )
        self.instance_manager = InstanceManager(self.platform_client)


class SmartGroup(click.Group):
    """Custom Click group that handles both subcommands and direct execution."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # List of known subcommands
        self.known_subcommands = {
            "run", "list-instances", "ls", "create-instance",
            "destroy-instance", "config-show", "config-set"
        }

    def resolve_command(self, ctx, args):
        """Resolve command, treating unknown commands as direct execution."""
        if not args:
            return super().resolve_command(ctx, args)

        cmd_name = args[0]

        # If it's a known subcommand, handle normally
        if cmd_name in self.known_subcommands:
            return super().resolve_command(ctx, args)

        # Otherwise, treat as direct execution - return the 'run' command
        # Store the args in ctx for the run command to access
        ctx.args = args  # Pass all args to the run command
        run_cmd = self.get_command(ctx, "run")
        return "run", run_cmd, []  # Return cmd_name, cmd, remaining_args

@click.group(cls=SmartGroup, invoke_without_command=True)
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--init", is_flag=True, help="Initialize configuration")
@click.option("--platform", "-p", type=click.Choice(["vast", "runpod", "auto"]), default="auto", help="Target platform")
@click.option("--instance-id", "-i", help="Specific instance ID to use")
@click.option("--sync-only", is_flag=True, help="Only sync files, don't run command")
@click.option("--no-sync", is_flag=True, help="Skip file synchronization")
@click.pass_context
def cli(ctx, config: str | None, verbose: bool, init: bool, platform: str, instance_id: str | None, sync_only: bool, no_sync: bool):  # noqa: ARG001
    """VariousPlug: Run code on remote Docker hosts (vast.ai and RunPod)."""

    setup_logging(verbose)

    ctx.ensure_object(dict)
    ctx.obj.update({
        "verbose": verbose,
        "platform": platform,
        "instance_id": instance_id,
        "sync_only": sync_only,
        "no_sync": no_sync
    })

    if init:
        initialize_config()
        return

    # If no subcommand is provided and no direct command, show help
    if ctx.invoked_subcommand is None and not getattr(ctx, "args", None):
        click.echo(ctx.get_help())


@cli.command()
@click.argument("command", nargs=-1, required=False)
@click.option("--dockerfile", "-d", help="Custom Dockerfile path")
@click.option("--working-dir", "-w", help="Working directory in container", default="/workspace")
@click.option("--enable-docker", is_flag=True, help="Enable Docker build step (disabled by default)")
@click.pass_context
def run(
    ctx,
    command: tuple,
    dockerfile: str | None,
    working_dir: str,
    enable_docker: bool,
):
    """Run a command on remote Docker host."""

    try:
        # Get options from context (set by main CLI or by direct options)
        platform = ctx.obj.get("platform", "auto")
        instance_id = ctx.obj.get("instance_id")
        sync_only = ctx.obj.get("sync_only", False)
        no_sync = ctx.obj.get("no_sync", False)

        # Handle smart routing - use ctx.args if command is empty (direct execution)
        if not command and hasattr(ctx, "args") and ctx.args:
            cmd_list = list(ctx.args)
        elif not command and hasattr(ctx.parent, "args") and ctx.parent.args:
            cmd_list = list(ctx.parent.args)
        else:
            cmd_list = list(command) if command else []

        if not cmd_list:
            click.echo("Error: No command specified")
            sys.exit(1)

        config_manager = ConfigManager.load()

        # Resolve platform
        if platform == "auto":
            platform = config_manager.get_default_platform()

        # Auto-select instance if not specified
        if not instance_id:
            instance_id = _auto_select_instance(config_manager, platform)

        # Create dependency container
        container = DependencyContainer(config_manager, platform)

        # Execute workflow
        result = container.workflow_executor.execute_workflow(
            command=cmd_list,
            platform=platform,
            instance_id=instance_id,
            sync_only=sync_only,
            no_sync=no_sync,
            dockerfile=dockerfile,
            working_dir=working_dir,
            enable_docker=enable_docker,
        )

        if result.success:
            print_success("Command executed successfully")
            if result.output:
                click.echo(result.output)
        else:
            print_error(f"Command failed: {result.error}")
            sys.exit(1)

    except Exception as e:
        print_error(f"Execution failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["vast", "runpod"]),
    help="Platform to list instances for (if not specified, shows all platforms)",
)
def list_instances(platform: str | None):
    """List available instances."""
    try:
        config_manager = ConfigManager.load()

        if platform:
            # List instances from specific platform
            container = DependencyContainer(config_manager, platform)
            instances = container.instance_manager.list_instances()

            if not instances:
                print_info(f"No instances found on {platform}")
                return

            for instance in instances:
                status_color = "green" if instance.status == InstanceStatus.RUNNING else "yellow"
                click.echo(f"ID: {instance.id}")
                click.echo(f"Platform: {instance.platform}")
                click.echo(f"Status: {click.style(instance.status.value, fg=status_color)}")
                click.echo(f"GPU: {instance.gpu_type or 'N/A'}")
                click.echo("---")
        else:
            # List instances from all enabled platforms
            all_instances = []
            platforms = ["vast", "runpod"]

            for plat in platforms:
                try:
                    platform_config = config_manager.get_platform_config(plat)
                    if platform_config.get("enabled", False) and platform_config.get("api_key"):
                        container = DependencyContainer(config_manager, plat)
                        instances = container.instance_manager.list_instances()
                        all_instances.extend(instances)
                except Exception:
                    # Skip platforms that fail (e.g., missing API key)
                    continue

            if not all_instances:
                print_info("No instances found on any platform")
                return

            # Sort instances by platform for better organization
            all_instances.sort(key=lambda x: (x.platform, x.id))

            for instance in all_instances:
                status_color = "green" if instance.status == InstanceStatus.RUNNING else "yellow"
                click.echo(f"ID: {instance.id}")
                click.echo(f"Platform: {instance.platform}")
                click.echo(f"Status: {click.style(instance.status.value, fg=status_color)}")
                click.echo(f"GPU: {instance.gpu_type or 'N/A'}")
                click.echo("---")

    except Exception as e:
        print_error(f"Failed to list instances: {e}")
        sys.exit(1)


# Add alias for list-instances
@cli.command(name="ls")
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["vast", "runpod"]),
    help="Platform to list instances for (if not specified, shows all platforms)",
)
def ls(platform: str | None):
    """List available instances (alias for list-instances)."""
    # Just call the main list_instances function
    ctx = click.get_current_context()
    ctx.invoke(list_instances, platform=platform)


@cli.command()
@click.option("--platform", "-p", type=click.Choice(["vast", "runpod"]), required=True)
@click.option("--gpu-type", help="GPU type to request")
@click.option("--instance-type", help="Instance type/size")
@click.option("--image", help="Docker image to use")
def create_instance(
    platform: str, gpu_type: str | None, instance_type: str | None, image: str | None
):
    """Create a new instance on the specified platform."""
    try:
        config_manager = ConfigManager.load()
        container = DependencyContainer(config_manager, platform)

        instance = container.instance_manager.create_instance(
            gpu_type=gpu_type, instance_type=instance_type, image=image
        )

        print_success(f"Instance created successfully: {instance.id}")
        click.echo(f"Platform: {instance.platform}")
        click.echo(f"Status: {instance.status.value}")

    except Exception as e:
        print_error(f"Failed to create instance: {e}")
        sys.exit(1)


@cli.command()
@click.argument("instance_id")
@click.option(
    "--platform", "-p", type=click.Choice(["vast", "runpod"]), help="Platform of the instance"
)
def destroy_instance(instance_id: str, platform: str | None):
    """Destroy an instance."""
    try:
        config_manager = ConfigManager.load()

        if not platform:
            platform = config_manager.get_default_platform()

        container = DependencyContainer(config_manager, platform)
        container.instance_manager.destroy_instance(instance_id)
        print_success(f"Instance {instance_id} destroyed successfully")

    except Exception as e:
        print_error(f"Failed to destroy instance: {e}")
        sys.exit(1)


@cli.command()
def config_show():
    """Show current configuration."""
    try:
        config_manager = ConfigManager.load()
        config_display = ConfigDisplay(config_manager)
        config_display.show()
    except Exception as e:
        print_error(f"Failed to show config: {e}")
        sys.exit(1)


@cli.command()
@click.option("--vast-api-key", help="Vast.ai API key")
@click.option("--runpod-api-key", help="RunPod API key")
@click.option(
    "--default-platform", type=click.Choice(["vast", "runpod"]), help="Default platform to use"
)
def config_set(vast_api_key: str | None, runpod_api_key: str | None, default_platform: str | None):
    """Set configuration values."""
    try:
        config_manager = ConfigManager.load()

        if vast_api_key:
            config_manager.update_platform_config(
                "vast", {"api_key": vast_api_key, "enabled": True}
            )
        if runpod_api_key:
            config_manager.update_platform_config(
                "runpod", {"api_key": runpod_api_key, "enabled": True}
            )
        if default_platform:
            config_manager.set_default_platform(default_platform)

        config_manager.save()
        print_success("Configuration updated successfully")

    except Exception as e:
        print_error(f"Failed to update config: {e}")
        sys.exit(1)


def initialize_config():
    """Initialize configuration interactively."""
    print_info("Initializing VariousPlug configuration...")

    # Get project name
    project_name = click.prompt("Enter your project name", default=Path.cwd().name)

    # Get API keys
    vast_api_key = click.prompt(
        "Enter your Vast.ai API key (optional)", default="", show_default=False
    )
    runpod_api_key = click.prompt(
        "Enter your RunPod API key (optional)", default="", show_default=False
    )

    # Get default platform
    default_platform = click.prompt(
        "Default platform", type=click.Choice(["vast", "runpod"]), default="vast"
    )

    # Get data directory
    data_dir = click.prompt("Data directory", default="data")

    # Get base Docker image
    base_image = click.prompt("Base Docker image", default="python:3.11-slim")

    try:
        config_manager = ConfigManager.create_new(
            project_name=project_name,
            vast_api_key=vast_api_key or None,
            runpod_api_key=runpod_api_key or None,
            default_platform=default_platform,
            data_dir=data_dir,
            base_image=base_image,
        )

        config_manager.save()

        # Create default files
        project_config = config_manager.get_project_config()
        sync_config = config_manager.get_sync_config()

        ConfigFileGenerator.create_dockerfile(project_config.get("base_image", "python:3.11-slim"))
        ConfigFileGenerator.create_vpignore(sync_config.get("exclude_patterns", []))

        print_success("Configuration initialized successfully!")
        print_info("Created files:")
        print_info("  - .vp/config.yaml (configuration)")
        print_info("  - Dockerfile (Docker image definition)")
        print_info("  - .vpignore (files to ignore during sync)")

    except Exception as e:
        print_error(f"Failed to initialize config: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
