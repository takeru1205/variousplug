"""
Abstract interfaces for VariousPlug following SOLID principles.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .utils import ExecutionResult


class InstanceStatus(Enum):
    """Standard instance status enumeration."""
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class InstanceInfo:
    """Standardized instance information."""
    id: str
    platform: str
    status: InstanceStatus
    gpu_type: str | None = None
    image: str | None = None
    ssh_host: str | None = None
    ssh_port: int | None = None
    ssh_username: str | None = None
    raw_data: dict[str, Any] | None = None


@dataclass
class CreateInstanceRequest:
    """Request object for creating instances."""
    gpu_type: str | None = None
    instance_type: str | None = None
    image: str | None = None
    additional_params: dict[str, Any] | None = None


class IPlatformClient(ABC):
    """Interface for platform clients (Interface Segregation Principle)."""

    @abstractmethod
    def list_instances(self) -> list[InstanceInfo]:
        """List all instances on the platform."""
        pass

    @abstractmethod
    def get_instance(self, instance_id: str) -> InstanceInfo | None:
        """Get specific instance details."""
        pass

    @abstractmethod
    def create_instance(self, request: CreateInstanceRequest) -> InstanceInfo:
        """Create a new instance."""
        pass

    @abstractmethod
    def destroy_instance(self, instance_id: str) -> bool:
        """Destroy an instance."""
        pass

    @abstractmethod
    def execute_command(self, instance_id: str, command: list[str]) -> ExecutionResult:
        """Execute a command on an instance."""
        pass

    @abstractmethod
    def wait_for_instance_ready(self, instance_id: str, timeout: int = 300) -> bool:
        """Wait for instance to be ready."""
        pass


class IFileSync(ABC):
    """Interface for file synchronization (Interface Segregation Principle)."""

    @abstractmethod
    def upload_files(self, instance_info: InstanceInfo, local_path: str,
                    remote_path: str, exclude_patterns: list[str]) -> bool:
        """Upload files to remote instance."""
        pass

    @abstractmethod
    def download_files(self, instance_info: InstanceInfo, remote_path: str,
                      local_path: str) -> bool:
        """Download files from remote instance."""
        pass


class IDockerBuilder(ABC):
    """Interface for Docker operations (Interface Segregation Principle)."""

    @abstractmethod
    def build_image(self, dockerfile_path: str, build_context: str,
                   tag: str, build_args: dict[str, str] | None = None) -> str | None:
        """Build Docker image."""
        pass

    @abstractmethod
    def image_exists(self, tag: str) -> bool:
        """Check if image exists."""
        pass


class IConfigManager(ABC):
    """Interface for configuration management (Interface Segregation Principle)."""

    @abstractmethod
    def get_project_config(self) -> dict[str, Any]:
        """Get project configuration."""
        pass

    @abstractmethod
    def get_platform_config(self, platform: str) -> dict[str, Any]:
        """Get platform-specific configuration."""
        pass

    @abstractmethod
    def get_docker_config(self) -> dict[str, Any]:
        """Get Docker configuration."""
        pass

    @abstractmethod
    def get_sync_config(self) -> dict[str, Any]:
        """Get file sync configuration."""
        pass


class IPlatformFactory(ABC):
    """Factory interface for creating platform clients (Abstract Factory Pattern)."""

    @abstractmethod
    def create_client(self, platform: str, config: dict[str, Any]) -> IPlatformClient:
        """Create platform client."""
        pass

    @abstractmethod
    def create_file_sync(self, platform: str, config: dict[str, Any] = None) -> IFileSync:
        """Create file sync client."""
        pass

    @abstractmethod
    def get_supported_platforms(self) -> list[str]:
        """Get list of supported platforms."""
        pass


class IWorkflowExecutor(ABC):
    """Interface for workflow execution (Single Responsibility Principle)."""

    @abstractmethod
    def execute_workflow(self, command: list[str], platform: str,
                        instance_id: str | None = None,
                        sync_only: bool = False, no_sync: bool = False,
                        dockerfile: str | None = None,
                        working_dir: str = "/workspace") -> ExecutionResult:
        """Execute the complete workflow."""
        pass
