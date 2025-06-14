"""
Core executor for VariousPlug implementing SOLID principles with dependency injection.
"""
import logging
import time
from pathlib import Path

from .interfaces import (
    CreateInstanceRequest,
    IConfigManager,
    IDockerBuilder,
    IFileSync,
    InstanceInfo,
    InstanceStatus,
    IPlatformClient,
    IWorkflowExecutor,
)
from .utils import (
    ExecutionResult,
    format_duration,
    print_error,
    print_info,
    print_success,
    print_warning,
    validate_command,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor(IWorkflowExecutor):
    """Main workflow executor following SOLID principles with dependency injection."""

    def __init__(self, config_manager: IConfigManager, platform_client: IPlatformClient,
                 file_sync: IFileSync, docker_builder: IDockerBuilder):
        """Dependency injection following Dependency Inversion Principle."""
        self.config_manager = config_manager
        self.platform_client = platform_client
        self.file_sync = file_sync
        self.docker_builder = docker_builder

    def execute_workflow(self, command: list[str], platform: str,
                        instance_id: str | None = None, sync_only: bool = False,
                        no_sync: bool = False, dockerfile: str | None = None,
                        working_dir: str = "/workspace") -> ExecutionResult:
        """Execute the complete BSRS workflow."""

        if not validate_command(command):
            return ExecutionResult(False, error="Invalid or unsafe command")

        start_time = time.time()

        try:
            # Step 1: Resolve target instance
            target_instance = self._resolve_target_instance(instance_id)
            if not target_instance and not sync_only:
                return ExecutionResult(False, error="No instance available for execution")

            print_info(f"Target: {platform} (instance: {target_instance.id if target_instance else 'auto'})")

            # Step 2: Build Docker image
            image_tag = None
            if not no_sync:
                image_tag = self._build_step(dockerfile)
                if not image_tag:
                    return ExecutionResult(False, error="Build step failed")

            # Step 3: Sync files to remote
            if not no_sync and target_instance:
                sync_result = self._sync_step_upload(target_instance)
                if not sync_result:
                    return ExecutionResult(False, error="Upload sync step failed")

            # Step 4: Run command (unless sync-only)
            if sync_only:
                print_success("Sync completed successfully")
                return ExecutionResult(True, "Files synchronized")

            if not target_instance:
                return ExecutionResult(False, error="No instance available for command execution")

            run_result = self._run_step(command, target_instance, working_dir)

            # Step 5: Sync files back from remote
            if not no_sync:
                self._sync_step_download(target_instance)

            duration = time.time() - start_time
            print_success(f"Execution completed in {format_duration(duration)}")

            return run_result

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return ExecutionResult(False, error=str(e))

    def _resolve_target_instance(self, instance_id: str | None) -> InstanceInfo | None:
        """Resolve target instance using strategy pattern."""
        if instance_id:
            return self.platform_client.get_instance(instance_id)

        # Auto-select instance
        instances = self.platform_client.list_instances()

        # Strategy 1: Find running instance
        running_instances = [i for i in instances if i.status == InstanceStatus.RUNNING]
        if running_instances:
            selected = running_instances[0]
            print_info(f"Auto-selected running instance: {selected.id}")
            return selected

        # Strategy 2: Find available instance
        available_instances = [i for i in instances if i.status in [InstanceStatus.STOPPED, InstanceStatus.PENDING]]
        if available_instances:
            selected = available_instances[0]
            print_info(f"Auto-selected available instance: {selected.id}")
            return selected

        return None

    def _build_step(self, dockerfile: str | None = None) -> str | None:
        """Build Docker image step."""
        print_info("🔨 Build step: Building Docker image...")

        docker_config = self.config_manager.get_docker_config()
        project_config = self.config_manager.get_project_config()

        dockerfile_path = dockerfile or docker_config.get("dockerfile", "Dockerfile")
        build_context = docker_config.get("build_context", ".")
        build_args = docker_config.get("build_args", {})

        if not Path(dockerfile_path).exists():
            print_warning(f"Dockerfile not found: {dockerfile_path}")
            return None

        project_name = project_config.get("name", "unknown")
        image_tag = f"vp-{project_name}:latest"

        return self.docker_builder.build_image(dockerfile_path, build_context, image_tag, build_args)

    def _sync_step_upload(self, instance: InstanceInfo) -> bool:
        """Sync files to remote (upload)."""
        print_info("📤 Sync step: Uploading files to remote...")

        try:
            sync_config = self.config_manager.get_sync_config()
            exclude_patterns = sync_config.get("exclude_patterns", [])

            local_path = "."
            remote_path = "/workspace"

            return self.file_sync.upload_files(instance, local_path, remote_path, exclude_patterns)

        except Exception as e:
            print_error(f"Upload sync failed: {e}")
            return False

    def _sync_step_download(self, instance: InstanceInfo) -> bool:
        """Sync files from remote (download)."""
        print_info("📥 Sync step: Downloading files from remote...")

        try:
            project_config = self.config_manager.get_project_config()
            data_dir = project_config.get("data_dir", "data")

            remote_path = f"/workspace/{data_dir}"
            local_path = f"./{data_dir}"

            return self.file_sync.download_files(instance, remote_path, local_path)

        except Exception as e:
            print_error(f"Download sync failed: {e}")
            return False

    def _run_step(self, command: list[str], instance: InstanceInfo, working_dir: str) -> ExecutionResult:
        """Run command on remote."""
        print_info(f"🚀 Run step: Executing command: {' '.join(command)}")

        try:
            return self.platform_client.execute_command(instance.id, command)
        except Exception as e:
            return ExecutionResult(False, error=str(e))


class InstanceManager:
    """Separate class for instance management operations (Single Responsibility)."""

    def __init__(self, platform_client: IPlatformClient):
        self.platform_client = platform_client

    def list_instances(self) -> list[InstanceInfo]:
        """List instances."""
        return self.platform_client.list_instances()

    def create_instance(self, gpu_type: str | None = None,
                       instance_type: str | None = None,
                       image: str | None = None) -> InstanceInfo:
        """Create instance."""
        request = CreateInstanceRequest(
            gpu_type=gpu_type,
            instance_type=instance_type,
            image=image
        )
        return self.platform_client.create_instance(request)

    def destroy_instance(self, instance_id: str) -> bool:
        """Destroy instance."""
        return self.platform_client.destroy_instance(instance_id)

    def wait_for_ready(self, instance_id: str, timeout: int = 300) -> bool:
        """Wait for instance to be ready."""
        return self.platform_client.wait_for_instance_ready(instance_id, timeout)
