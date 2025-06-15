"""
Base classes implementing common functionality (DRY Principle).
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from .interfaces import (
    IDockerBuilder,
    IFileSync,
    InstanceInfo,
    InstanceStatus,
    IPlatformClient,
)
from .utils import print_error, print_info, print_warning

logger = logging.getLogger(__name__)


class BasePlatformClient(IPlatformClient):
    """Base platform client with common functionality (Template Method Pattern)."""

    def __init__(self, api_key: str, platform_name: str):
        self.api_key = api_key
        self.platform_name = platform_name
        self._client = None

    def _initialize_client(self):
        """Template method for client initialization."""
        if self._client is None:
            self._client = self._create_client()

    def _create_client(self):
        """Abstract method for creating platform-specific client."""
        raise NotImplementedError("Subclasses must implement _create_client")

    def _normalize_status(self, raw_status: str | None) -> InstanceStatus:
        """Common status normalization logic."""
        if raw_status is None:
            return InstanceStatus.UNKNOWN
        status_map = {
            "running": InstanceStatus.RUNNING,
            "ready": InstanceStatus.RUNNING,
            "pending": InstanceStatus.PENDING,
            "loading": InstanceStatus.STARTING,
            "initializing": InstanceStatus.STARTING,
            "starting": InstanceStatus.STARTING,
            "created": InstanceStatus.STOPPED,
            "stopped": InstanceStatus.STOPPED,
            "exited": InstanceStatus.STOPPED,
            "terminated": InstanceStatus.STOPPED,
            "error": InstanceStatus.ERROR,
            "failed": InstanceStatus.ERROR,
        }
        result = status_map.get(raw_status.lower())
        return result if result is not None else InstanceStatus.UNKNOWN

    def _create_instance_info(self, raw_data: dict[str, Any]) -> InstanceInfo:
        """Template method for creating standardized instance info."""
        return InstanceInfo(
            id=str(raw_data.get("id", "unknown")),
            platform=self.platform_name,
            status=self._normalize_status(raw_data.get("status", "unknown")),
            gpu_type=raw_data.get("gpu_type") or raw_data.get("gpu_name"),
            image=raw_data.get("image"),
            ssh_host=raw_data.get("ssh_host"),
            ssh_port=raw_data.get("ssh_port"),
            ssh_username=raw_data.get("ssh_username", "root"),
            raw_data=raw_data,
        )

    def wait_for_instance_ready(self, instance_id: str, timeout: int = 300) -> bool:
        """Common implementation for waiting for instance readiness."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            instance = self.get_instance(instance_id)
            if (
                instance
                and instance.status == InstanceStatus.RUNNING
                and self._is_instance_ready(instance)
            ):
                print_info(f"Instance {instance_id} is ready")
                return True

            print_info(f"Waiting for instance {instance_id} to be ready...")
            time.sleep(10)

        print_warning(f"Instance {instance_id} did not become ready within {timeout}s")
        return False

    def _is_instance_ready(self, _instance: InstanceInfo) -> bool:
        """Hook for platform-specific readiness checks."""
        return True  # Default implementation


class RsyncFileSync(IFileSync):
    """Rsync-based file synchronization implementation."""

    def upload_files(
        self,
        instance_info: InstanceInfo,
        local_path: str,
        remote_path: str,
        exclude_patterns: list[str],
    ) -> bool:
        """Upload files using rsync."""
        try:
            if not instance_info.ssh_host or not instance_info.ssh_port:
                print_error("SSH connection info not available")
                return False

            rsync_cmd = [
                "rsync",
                "-avz",
                "--progress",
                "-e",
                f"ssh -p {instance_info.ssh_port} -o StrictHostKeyChecking=no",
                f"{local_path}/",
                f"{instance_info.ssh_username}@{instance_info.ssh_host}:{remote_path}/",
            ]

            # Add exclude patterns
            for pattern in exclude_patterns:
                rsync_cmd.extend(["--exclude", pattern])

            print_info(
                f"Uploading to {instance_info.ssh_username}@{instance_info.ssh_host}:{instance_info.ssh_port}"
            )

            result = subprocess.run(rsync_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print_info("Files uploaded successfully")
                return True
            else:
                print_error(f"Upload failed: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Upload sync failed: {e}")
            return False

    def download_files(
        self, instance_info: InstanceInfo, remote_path: str, local_path: str
    ) -> bool:
        """Download files using rsync."""
        try:
            if not instance_info.ssh_host or not instance_info.ssh_port:
                print_error("SSH connection info not available")
                return False

            rsync_cmd = [
                "rsync",
                "-avz",
                "--progress",
                "-e",
                f"ssh -p {instance_info.ssh_port} -o StrictHostKeyChecking=no",
                f"{instance_info.ssh_username}@{instance_info.ssh_host}:{remote_path}/",
                f"{local_path}/",
            ]

            print_info(
                f"Downloading from {instance_info.ssh_username}@{instance_info.ssh_host}:{instance_info.ssh_port}"
            )

            result = subprocess.run(rsync_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print_info("Files downloaded successfully")
                return True
            else:
                print_warning(f"Download completed with warnings: {result.stderr}")
                return True  # Don't fail on download warnings

        except Exception as e:
            print_error(f"Download sync failed: {e}")
            return False


class DockerBuilder(IDockerBuilder):
    """Docker builder implementation."""

    def __init__(self):
        self._docker_client = None

    def _get_docker_client(self):
        """Lazy initialization of Docker client."""
        if self._docker_client is None:
            import docker

            try:
                self._docker_client = docker.from_env()
            except Exception as e:
                logger.error(f"Failed to initialize Docker client: {e}")
                raise
        return self._docker_client

    def build_image(
        self,
        dockerfile_path: str,
        build_context: str,
        tag: str,
        build_args: dict[str, str] | None = None,
    ) -> str | None:
        """Build Docker image."""
        try:
            client = self._get_docker_client()

            if not Path(dockerfile_path).exists():
                print_warning(f"Dockerfile not found: {dockerfile_path}")
                return None

            print_info(f"Building image: {tag}")

            image, logs = client.images.build(
                path=build_context,
                dockerfile=dockerfile_path,
                tag=tag,
                buildargs=build_args or {},
                rm=True,
            )

            # Log build output if verbose
            for log in logs:
                if "stream" in log:
                    logger.debug(log["stream"].strip())

            print_info(f"Image built successfully: {tag}")
            return tag

        except Exception as e:
            print_error(f"Build failed: {e}")
            return None

    def image_exists(self, tag: str) -> bool:
        """Check if image exists."""
        try:
            client = self._get_docker_client()
            client.images.get(tag)
            return True
        except Exception:
            return False


class NoOpFileSync(IFileSync):
    """No-operation file sync for platforms that don't support it."""

    def upload_files(
        self,
        instance_info: InstanceInfo,
        _local_path: str,
        _remote_path: str,
        _exclude_patterns: list[str],
    ) -> bool:
        """No-op upload."""
        print_warning(f"File sync not supported for platform {instance_info.platform}")
        return True

    def download_files(
        self, instance_info: InstanceInfo, _remote_path: str, _local_path: str
    ) -> bool:
        """No-op download."""
        print_warning(f"File sync not supported for platform {instance_info.platform}")
        return True


class VastFileSync(IFileSync):
    """Vast.ai rsync-based file synchronization implementation."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Note: For rsync, we don't need the SDK client

    def upload_files(
        self,
        instance_info: InstanceInfo,
        local_path: str,
        remote_path: str,
        exclude_patterns: list[str],
    ) -> bool:
        """Upload files using rsync over SSH."""
        try:
            if not instance_info.ssh_host or not instance_info.ssh_port:
                print_error("SSH connection info not available")
                return False

            print_info(
                f"Uploading to {instance_info.ssh_username}@{instance_info.ssh_host}:{instance_info.ssh_port}"
            )

            # Build rsync command with exclusions
            rsync_cmd = [
                "rsync",
                "-avz",  # archive, verbose, compress
                "--delete",  # delete files on remote that don't exist locally
                "--progress",
            ]

            # Add exclude patterns
            for pattern in exclude_patterns:
                rsync_cmd.extend(["--exclude", pattern])

            # Add SSH options
            ssh_options = [
                "-p",
                str(instance_info.ssh_port),
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "LogLevel=ERROR",
            ]
            rsync_cmd.extend(["-e", f"ssh {' '.join(ssh_options)}"])

            # Add source and destination
            rsync_cmd.append(f"{local_path}/")
            rsync_cmd.append(
                f"{instance_info.ssh_username}@{instance_info.ssh_host}:{remote_path}/"
            )

            # Execute rsync
            import subprocess

            result = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print_info("Files uploaded successfully")
                return True
            else:
                print_error(f"Upload failed: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Upload sync failed: {e}")
            return False

    def download_files(
        self, instance_info: InstanceInfo, remote_path: str, local_path: str
    ) -> bool:
        """Download files using rsync over SSH."""
        try:
            if not instance_info.ssh_host or not instance_info.ssh_port:
                print_error("SSH connection info not available")
                return False

            print_info(
                f"Downloading from {instance_info.ssh_username}@{instance_info.ssh_host}:{instance_info.ssh_port}"
            )

            # Ensure local directory exists
            Path(local_path).mkdir(parents=True, exist_ok=True)

            # Build rsync command
            rsync_cmd = [
                "rsync",
                "-avz",  # archive, verbose, compress
                "--progress",
            ]

            # Add SSH options
            ssh_options = [
                "-p",
                str(instance_info.ssh_port),
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "LogLevel=ERROR",
            ]
            rsync_cmd.extend(["-e", f"ssh {' '.join(ssh_options)}"])

            # Add source and destination
            rsync_cmd.append(
                f"{instance_info.ssh_username}@{instance_info.ssh_host}:{remote_path}/"
            )
            rsync_cmd.append(f"{local_path}/")

            # Execute rsync
            import subprocess

            result = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print_info("Files downloaded successfully")
                return True
            elif result.returncode == 23 or result.returncode == 24:
                # rsync exit codes 23 and 24 are partial transfers (warnings)
                print_warning(f"Download completed with warnings: {result.stderr}")
                return True
            else:
                print_error(f"Download failed: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Download sync failed: {e}")
            return False
