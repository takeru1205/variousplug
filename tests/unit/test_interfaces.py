"""
Unit tests for VariousPlug interfaces.
"""

from typing import Any

from variousplug.interfaces import (
    CreateInstanceRequest,
    IConfigManager,
    IDockerBuilder,
    IFileSync,
    InstanceInfo,
    InstanceStatus,
    IPlatformClient,
    IPlatformFactory,
)
from variousplug.utils import ExecutionResult


class TestInstanceInfo:
    """Test InstanceInfo dataclass."""

    def test_instance_info_creation(self):
        """Test creating InstanceInfo."""
        instance = InstanceInfo(
            id="test_123",
            platform="vast",
            status=InstanceStatus.RUNNING,
            gpu_type="GTX_1080",
            image="pytorch/pytorch",
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root",
            raw_data={"test": "data"},
        )

        assert instance.id == "test_123"
        assert instance.platform == "vast"
        assert instance.status == InstanceStatus.RUNNING
        assert instance.gpu_type == "GTX_1080"
        assert instance.image == "pytorch/pytorch"
        assert instance.ssh_host == "test.host"
        assert instance.ssh_port == 22
        assert instance.ssh_username == "root"
        assert instance.raw_data == {"test": "data"}

    def test_instance_info_defaults(self):
        """Test InstanceInfo with minimal parameters."""
        instance = InstanceInfo(id="test_456", platform="runpod", status=InstanceStatus.PENDING)

        assert instance.id == "test_456"
        assert instance.platform == "runpod"
        assert instance.status == InstanceStatus.PENDING
        assert instance.gpu_type is None
        assert instance.image is None
        assert instance.ssh_host is None
        assert instance.ssh_port is None
        assert instance.ssh_username is None
        assert instance.raw_data is None


class TestInstanceStatus:
    """Test InstanceStatus enum."""

    def test_instance_status_values(self):
        """Test all InstanceStatus values."""
        assert InstanceStatus.PENDING.value == "pending"
        assert InstanceStatus.RUNNING.value == "running"
        assert InstanceStatus.STOPPED.value == "stopped"
        assert InstanceStatus.UNKNOWN.value == "unknown"

    def test_instance_status_comparison(self):
        """Test InstanceStatus comparison."""
        assert InstanceStatus.RUNNING == InstanceStatus.RUNNING
        assert InstanceStatus.PENDING != InstanceStatus.RUNNING


class TestCreateInstanceRequest:
    """Test CreateInstanceRequest dataclass."""

    def test_create_request_creation(self):
        """Test creating CreateInstanceRequest."""
        request = CreateInstanceRequest(
            gpu_type="RTX_4090",
            image="pytorch/pytorch:latest",
            instance_type="gpu",
            additional_params={"memory": "32GB"},
        )

        assert request.gpu_type == "RTX_4090"
        assert request.image == "pytorch/pytorch:latest"
        assert request.instance_type == "gpu"
        assert request.additional_params == {"memory": "32GB"}

    def test_create_request_defaults(self):
        """Test CreateInstanceRequest with defaults."""
        request = CreateInstanceRequest()

        assert request.gpu_type is None
        assert request.image is None
        assert request.instance_type is None
        assert request.additional_params is None


class MockPlatformClient(IPlatformClient):
    """Mock implementation of IPlatformClient for testing."""

    def __init__(self):
        self.instances = []

    def list_instances(self) -> list[InstanceInfo]:
        return self.instances

    def get_instance(self, instance_id: str) -> InstanceInfo:
        for instance in self.instances:
            if instance.id == instance_id:
                return instance
        return None

    def create_instance(self, request: CreateInstanceRequest) -> InstanceInfo:
        instance = InstanceInfo(
            id=f"mock_{len(self.instances)}",
            platform="mock",
            status=InstanceStatus.PENDING,
            gpu_type=request.gpu_type,
            image=request.image,
        )
        self.instances.append(instance)
        return instance

    def destroy_instance(self, instance_id: str) -> bool:
        self.instances = [i for i in self.instances if i.id != instance_id]
        return True

    def execute_command(self, instance_id: str, command: list[str]) -> ExecutionResult:
        return ExecutionResult(True, "Mock command executed")

    def wait_for_instance_ready(self, instance_id: str, timeout: int = 300) -> bool:
        return True


class TestIPlatformClient:
    """Test IPlatformClient interface."""

    def test_platform_client_interface(self):
        """Test platform client interface implementation."""
        client = MockPlatformClient()

        # Test empty list
        assert client.list_instances() == []

        # Test create instance
        request = CreateInstanceRequest(gpu_type="GTX_1080", image="test:latest")
        instance = client.create_instance(request)

        assert instance.id == "mock_0"
        assert instance.platform == "mock"
        assert instance.status == InstanceStatus.PENDING
        assert instance.gpu_type == "GTX_1080"
        assert instance.image == "test:latest"

        # Test list instances
        instances = client.list_instances()
        assert len(instances) == 1
        assert instances[0].id == "mock_0"

        # Test get specific instance
        retrieved = client.get_instance("mock_0")
        assert retrieved is not None
        assert retrieved.id == "mock_0"

        # Test get non-existent instance
        not_found = client.get_instance("nonexistent")
        assert not_found is None

        # Test destroy instance
        success = client.destroy_instance("mock_0")
        assert success is True
        assert client.list_instances() == []


class MockFileSync(IFileSync):
    """Mock implementation of IFileSync for testing."""

    def __init__(self):
        self.uploaded_files = []
        self.downloaded_files = []

    def upload_files(
        self,
        instance_info: InstanceInfo,
        local_path: str,
        remote_path: str,
        exclude_patterns: list[str] | None = None,
    ) -> bool:
        self.uploaded_files.append((instance_info, local_path, remote_path, exclude_patterns))
        return True

    def download_files(
        self, instance_info: InstanceInfo, remote_path: str, local_path: str
    ) -> bool:
        self.downloaded_files.append((instance_info, remote_path, local_path))
        return True


class TestIFileSync:
    """Test IFileSync interface."""

    def test_file_sync_interface(self):
        """Test file sync interface implementation."""
        sync = MockFileSync()
        instance = InstanceInfo(id="test", platform="test", status=InstanceStatus.RUNNING)

        # Test upload
        success = sync.upload_files(instance, "/local/path", "/remote/path", ["*.pyc"])
        assert success is True
        assert len(sync.uploaded_files) == 1
        assert sync.uploaded_files[0] == (instance, "/local/path", "/remote/path", ["*.pyc"])

        # Test download
        success = sync.download_files(instance, "/remote/path", "/local/path")
        assert success is True
        assert len(sync.downloaded_files) == 1
        assert sync.downloaded_files[0] == (instance, "/remote/path", "/local/path")


class MockDockerBuilder(IDockerBuilder):
    """Mock implementation of IDockerBuilder for testing."""

    def __init__(self):
        self.built_images = []

    def build_image(
        self,
        dockerfile_path: str,
        build_context: str,
        tag: str,
        build_args: dict[str, str] | None = None,
    ) -> str | None:
        self.built_images.append((dockerfile_path, build_context, tag, build_args))
        return f"built:{tag}"

    def image_exists(self, tag: str) -> bool:
        return any(built_tag == tag for _, _, built_tag, _ in self.built_images)


class TestIDockerBuilder:
    """Test IDockerBuilder interface."""

    def test_docker_builder_interface(self):
        """Test docker builder interface implementation."""
        builder = MockDockerBuilder()

        # Test build image
        image_id = builder.build_image("Dockerfile", ".", "test:latest", {"ARG1": "value1"})
        assert image_id == "built:test:latest"
        assert len(builder.built_images) == 1
        assert builder.built_images[0] == ("Dockerfile", ".", "test:latest", {"ARG1": "value1"})

        # Test image exists
        exists = builder.image_exists("test:latest")
        assert exists is True

        # Test image doesn't exist
        not_exists = builder.image_exists("nonexistent:latest")
        assert not_exists is False


class MockConfigManager(IConfigManager):
    """Mock implementation of IConfigManager for testing."""

    def __init__(self):
        self.config = {}

    def get_project_config(self) -> dict[str, Any]:
        return self.config.get("project", {})

    def get_platform_config(self, platform: str) -> dict[str, Any]:
        return self.config.get("platforms", {}).get(platform, {})

    def get_docker_config(self) -> dict[str, Any]:
        return self.config.get("docker", {})

    def get_sync_config(self) -> dict[str, Any]:
        return self.config.get("sync", {})

    def update_platform_config(self, platform: str, config: dict):
        if "platforms" not in self.config:
            self.config["platforms"] = {}
        self.config["platforms"][platform] = config

    def get_default_platform(self):
        return self.config.get("platforms", {}).get("default", "vast")

    def set_default_platform(self, platform: str):
        if "platforms" not in self.config:
            self.config["platforms"] = {}
        self.config["platforms"]["default"] = platform


class TestIConfigManager:
    """Test IConfigManager interface."""

    def test_config_manager_interface(self):
        """Test config manager interface implementation."""
        manager = MockConfigManager()

        # Test initial state
        assert manager.get_default_platform() == "vast"
        assert manager.get_platform_config("vast") == {}

        # Test update platform config
        manager.update_platform_config("vast", {"api_key": "test_key", "enabled": True})
        config = manager.get_platform_config("vast")
        assert config == {"api_key": "test_key", "enabled": True}

        # Test set default platform
        manager.set_default_platform("runpod")
        assert manager.get_default_platform() == "runpod"


class MockPlatformFactory(IPlatformFactory):
    """Mock implementation of IPlatformFactory for testing."""

    def create_client(self, platform: str, config: dict) -> IPlatformClient:
        return MockPlatformClient()

    def create_file_sync(self, platform: str) -> IFileSync:
        return MockFileSync()

    def get_supported_platforms(self) -> list[str]:
        return ["vast", "runpod"]


class TestIPlatformFactory:
    """Test IPlatformFactory interface."""

    def test_platform_factory_interface(self):
        """Test platform factory interface implementation."""
        factory = MockPlatformFactory()

        # Test create client
        client = factory.create_client("vast", {"api_key": "test"})
        assert isinstance(client, MockPlatformClient)

        # Test create file sync
        sync = factory.create_file_sync("vast")
        assert isinstance(sync, MockFileSync)

        # Test get supported platforms
        platforms = factory.get_supported_platforms()
        assert platforms == ["vast", "runpod"]
