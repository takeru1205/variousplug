"""
Pytest configuration and fixtures for VariousPlug tests.
"""
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from variousplug.config import ConfigManager
from variousplug.interfaces import CreateInstanceRequest, InstanceInfo, InstanceStatus


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config_dir(temp_dir):
    """Create a mock .vp directory."""
    config_dir = temp_dir / ".vp"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        "project": {
            "name": "test-project",
            "data_dir": "data",
            "base_image": "python:3.11-slim",
            "working_dir": "/workspace"
        },
        "platforms": {
            "default": "vast",
            "vast": {
                "api_key": "test_vast_key",
                "enabled": True
            },
            "runpod": {
                "api_key": "test_runpod_key",
                "enabled": True
            }
        },
        "docker": {
            "build_context": ".",
            "dockerfile": "Dockerfile",
            "build_args": {}
        },
        "sync": {
            "exclude_patterns": [".git/", ".vp/", "*.pyc"],
            "include_patterns": ["*"]
        }
    }


@pytest.fixture
def config_manager(mock_config_dir, sample_config):
    """Create a ConfigManager instance with test data."""
    config_file = mock_config_dir / "config.yaml"

    # Create config manager and save test config
    manager = ConfigManager(config_file)
    manager._data = sample_config
    manager.save()

    return manager


@pytest.fixture
def mock_instance_running():
    """Mock running instance."""
    return InstanceInfo(
        id="test_instance_123",
        platform="vast",
        status=InstanceStatus.RUNNING,
        gpu_type="GTX_1080",
        image="pytorch/pytorch",
        ssh_host="test.vast.ai",
        ssh_port=22,
        ssh_username="root",
        raw_data={"id": "test_instance_123", "status": "running"}
    )


@pytest.fixture
def mock_instance_pending():
    """Mock pending instance."""
    return InstanceInfo(
        id="test_instance_456",
        platform="runpod",
        status=InstanceStatus.PENDING,
        gpu_type="RTX_4090",
        image="runpod/pytorch:latest",
        raw_data={"id": "test_instance_456", "status": "pending"}
    )


@pytest.fixture
def sample_create_request():
    """Sample create instance request."""
    return CreateInstanceRequest(
        gpu_type="GTX_1080",
        image="pytorch/pytorch",
        instance_type="gpu",
        additional_params={}
    )


@pytest.fixture
def mock_vast_client():
    """Mock Vast.ai client."""
    client = Mock()
    client.show_instances.return_value = []
    client.launch_instance.return_value = {"new_contract": "test_instance_123"}
    client.destroy_instance.return_value = True
    return client


@pytest.fixture
def mock_runpod_client():
    """Mock RunPod client."""
    client = Mock()
    client.get_pods.return_value = []
    client.create_pod.return_value = {"id": "test_pod_123"}
    client.terminate_pod.return_value = True
    return client


@pytest.fixture
def mock_docker_client():
    """Mock Docker client."""
    client = Mock()
    client.images.build.return_value = (Mock(id="test_image"), [])
    return client


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for SSH and rsync commands."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Command executed successfully"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch, temp_dir):
    """Set up mock environment for all tests."""
    # Change to temp directory
    monkeypatch.chdir(temp_dir)

    # Mock environment variables
    monkeypatch.setenv("VP_TEST_MODE", "true")

    # Ensure no real API calls are made
    monkeypatch.setenv("VP_NO_API_CALLS", "true")


@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()


class MockPlatformClient:
    """Mock platform client for testing."""

    def __init__(self, platform_name="test"):
        self.platform_name = platform_name
        self.instances = []

    def list_instances(self):
        return self.instances

    def get_instance(self, instance_id):
        for instance in self.instances:
            if instance.id == instance_id:
                return instance
        return None

    def create_instance(self, request):
        instance = InstanceInfo(
            id=f"mock_{len(self.instances)}",
            platform=self.platform_name,
            status=InstanceStatus.PENDING,
            gpu_type=request.gpu_type,
            image=request.image,
            raw_data={"mock": True}
        )
        self.instances.append(instance)
        return instance

    def destroy_instance(self, instance_id):
        self.instances = [i for i in self.instances if i.id != instance_id]
        return True


@pytest.fixture
def mock_platform_client():
    """Mock platform client."""
    return MockPlatformClient()
