"""
Unit tests for VariousPlug base classes.
"""

import subprocess
from unittest.mock import Mock, patch

import docker
import pytest

from variousplug.base import BasePlatformClient, DockerBuilder, NoOpFileSync, RsyncFileSync
from variousplug.interfaces import InstanceInfo, InstanceStatus
from variousplug.utils import ExecutionResult


class TestBasePlatformClient:
    """Test BasePlatformClient abstract base class."""

    class ConcretePlatformClient(BasePlatformClient):
        """Concrete implementation for testing."""

        def __init__(self, api_key="test_key"):
            super().__init__(api_key, "test_platform")
            self.mock_client = Mock()

        def _create_client(self):
            return self.mock_client

        def list_instances(self):
            return [
                InstanceInfo(
                    id="test_1",
                    platform=self.platform_name,
                    status=InstanceStatus.RUNNING,
                    raw_data={"id": "test_1", "status": "running"},
                )
            ]

        def get_instance(self, instance_id):
            if instance_id == "test_1":
                return InstanceInfo(
                    id="test_1",
                    platform=self.platform_name,
                    status=InstanceStatus.RUNNING,
                    raw_data={"id": "test_1", "status": "running"},
                )
            elif instance_id == "test_ready":
                return InstanceInfo(
                    id="test_ready",
                    platform=self.platform_name,
                    status=InstanceStatus.RUNNING,
                    raw_data={"id": "test_ready", "status": "running"},
                )
            elif instance_id == "test_not_ready":
                return InstanceInfo(
                    id="test_not_ready",
                    platform=self.platform_name,
                    status=InstanceStatus.PENDING,
                    raw_data={"id": "test_not_ready", "status": "pending"},
                )
            return None

        def create_instance(self, request):
            return InstanceInfo(
                id="new_instance",
                platform=self.platform_name,
                status=InstanceStatus.PENDING,
                gpu_type=request.gpu_type,
                image=request.image,
                raw_data={"id": "new_instance", "status": "pending"},
            )

        def destroy_instance(self, instance_id):
            return True

        def execute_command(self, instance_id, command):
            return ExecutionResult(True, "Command executed successfully")

    def test_base_platform_client_init(self):
        """Test BasePlatformClient initialization."""
        client = self.ConcretePlatformClient("test_api_key")

        assert client.api_key == "test_api_key"
        assert client.platform_name == "test_platform"
        assert client._client is None

    def test_initialize_client(self):
        """Test client initialization."""
        client = self.ConcretePlatformClient()

        # Client should be None initially
        assert client._client is None

        # Initialize client
        client._initialize_client()

        # Client should now be set
        assert client._client is not None
        assert client._client == client.mock_client

    def test_initialize_client_once(self):
        """Test client is only initialized once."""
        client = self.ConcretePlatformClient()

        # Initialize twice
        client._initialize_client()
        first_client = client._client

        client._initialize_client()
        second_client = client._client

        # Should be the same instance
        assert first_client is second_client

    def test_normalize_status(self):
        """Test status normalization."""
        client = self.ConcretePlatformClient()

        # Test various status mappings
        assert client._normalize_status("running") == InstanceStatus.RUNNING
        assert client._normalize_status("RUNNING") == InstanceStatus.RUNNING
        assert client._normalize_status("ready") == InstanceStatus.RUNNING

        assert client._normalize_status("pending") == InstanceStatus.PENDING
        assert client._normalize_status("PENDING") == InstanceStatus.PENDING
        assert client._normalize_status("starting") == InstanceStatus.STARTING

        assert client._normalize_status("stopped") == InstanceStatus.STOPPED
        assert client._normalize_status("STOPPED") == InstanceStatus.STOPPED
        assert client._normalize_status("terminated") == InstanceStatus.STOPPED

        assert client._normalize_status("unknown_status") == InstanceStatus.UNKNOWN
        assert client._normalize_status("") == InstanceStatus.UNKNOWN
        assert client._normalize_status(None) == InstanceStatus.UNKNOWN

    def test_wait_for_instance_ready_success(self):
        """Test waiting for instance to be ready (success case)."""
        client = self.ConcretePlatformClient()

        # Mock instance that becomes ready
        _instance = InstanceInfo(
            id="test_ready", platform="test_platform", status=InstanceStatus.RUNNING
        )

        with patch.object(client, "_is_instance_ready", return_value=True):
            result = client.wait_for_instance_ready("test_ready", timeout=1)
            assert result is True

    def test_wait_for_instance_ready_timeout(self):
        """Test waiting for instance to be ready (timeout case)."""
        client = self.ConcretePlatformClient()

        # Mock instance that never becomes ready
        _instance = InstanceInfo(
            id="test_not_ready", platform="test_platform", status=InstanceStatus.PENDING
        )

        with patch.object(client, "_is_instance_ready", return_value=False):
            result = client.wait_for_instance_ready("test_not_ready", timeout=1)
            assert result is False

    def test_is_instance_ready_default(self):
        """Test default _is_instance_ready implementation."""
        client = self.ConcretePlatformClient()

        running_instance = InstanceInfo(
            id="running", platform="test_platform", status=InstanceStatus.RUNNING
        )

        pending_instance = InstanceInfo(
            id="pending", platform="test_platform", status=InstanceStatus.PENDING
        )

        assert client._is_instance_ready(running_instance) is True
        assert client._is_instance_ready(pending_instance) is True


class TestRsyncFileSync:
    """Test RsyncFileSync implementation."""

    def test_rsync_file_sync_init(self):
        """Test RsyncFileSync initialization."""
        sync = RsyncFileSync()
        assert sync is not None

    @patch("subprocess.run")
    def test_upload_files_success(self, mock_run):
        """Test successful file upload."""
        mock_run.return_value.returncode = 0

        sync = RsyncFileSync()
        instance_info = InstanceInfo(
            id="test-id",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="host",
            ssh_port=22,
            ssh_username="user",
        )
        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/remote/path",
            exclude_patterns=["*.pyc", ".git/"],
        )

        assert result is True
        mock_run.assert_called_once()

        # Check rsync command
        call_args = mock_run.call_args[0][0]
        assert "rsync" in call_args
        assert "--exclude" in call_args
        assert "*.pyc" in call_args
        assert ".git/" in call_args
        assert "/local/path/" in call_args
        assert "user@host:/remote/path/" in call_args

    @patch("subprocess.run")
    def test_upload_files_failure(self, mock_run):
        """Test failed file upload."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Connection failed"

        sync = RsyncFileSync()
        instance_info = InstanceInfo(
            id="test-id",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="host",
            ssh_port=22,
            ssh_username="user",
        )
        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/remote/path",
            exclude_patterns=[],
        )

        assert result is False

    @patch("subprocess.run")
    def test_download_files_success(self, mock_run):
        """Test successful file download."""
        mock_run.return_value.returncode = 0

        sync = RsyncFileSync()
        instance_info = InstanceInfo(
            id="test-id",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="host",
            ssh_port=22,
            ssh_username="user",
        )
        result = sync.download_files(
            instance_info=instance_info, remote_path="/remote/path", local_path="/local/path"
        )

        assert result is True
        mock_run.assert_called_once()

        # Check rsync command
        call_args = mock_run.call_args[0][0]
        assert "rsync" in call_args
        assert "user@host:/remote/path/" in call_args
        assert "/local/path/" in call_args

    @patch("subprocess.run")
    def test_download_files_failure(self, mock_run):
        """Test failed file download."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Permission denied"

        sync = RsyncFileSync()
        instance_info = InstanceInfo(
            id="test-id",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="host",
            ssh_port=22,
            ssh_username="user",
        )
        result = sync.download_files(
            instance_info=instance_info, remote_path="/remote/path", local_path="/local/path"
        )

        assert result is True  # Download returns True even with warnings

    @patch("subprocess.run")
    def test_rsync_timeout_handling(self, mock_run):
        """Test rsync timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("rsync", 30)

        sync = RsyncFileSync()
        instance_info = InstanceInfo(
            id="test-id",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="host",
            ssh_port=22,
            ssh_username="user",
        )
        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/remote/path",
            exclude_patterns=[],
        )

        assert result is False

    @patch("subprocess.run")
    def test_rsync_exception_handling(self, mock_run):
        """Test rsync exception handling."""
        mock_run.side_effect = Exception("Unexpected error")

        sync = RsyncFileSync()
        instance_info = InstanceInfo(
            id="test-id",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="host",
            ssh_port=22,
            ssh_username="user",
        )
        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/remote/path",
            exclude_patterns=[],
        )

        assert result is False


class TestNoOpFileSync:
    """Test NoOpFileSync implementation."""

    def test_noop_file_sync_init(self):
        """Test NoOpFileSync initialization."""
        sync = NoOpFileSync()
        assert sync is not None

    def test_upload_files_always_true(self):
        """Test NoOpFileSync upload always returns True."""
        sync = NoOpFileSync()
        instance_info = InstanceInfo(id="test-id", platform="test", status=InstanceStatus.RUNNING)

        result = sync.upload_files(instance_info, "/any/path", "/any/remote", [])
        assert result is True

    def test_download_files_always_true(self):
        """Test NoOpFileSync download always returns True."""
        sync = NoOpFileSync()
        instance_info = InstanceInfo(id="test-id", platform="test", status=InstanceStatus.RUNNING)

        result = sync.download_files(instance_info, "/any/remote", "/any/local")
        assert result is True


class TestDockerBuilder:
    """Test DockerBuilder implementation."""

    def test_docker_builder_init(self):
        """Test DockerBuilder initialization."""
        builder = DockerBuilder()
        assert builder._docker_client is None

    @patch("docker.from_env")
    def test_initialize_client(self, mock_docker):
        """Test Docker client initialization."""
        mock_client = Mock()
        mock_docker.return_value = mock_client

        builder = DockerBuilder()
        builder._get_docker_client()

        assert builder._docker_client == mock_client
        mock_docker.assert_called_once()

    @patch("variousplug.base.Path")
    @patch("docker.from_env")
    def test_build_image_success(self, mock_docker, mock_path):
        """Test successful Docker image build."""
        mock_client = Mock()
        mock_docker.return_value = mock_client

        mock_image = Mock()
        mock_image.id = "sha256:abcd1234"
        mock_client.images.build.return_value = (mock_image, [])

        # Mock Path.exists to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        builder = DockerBuilder()
        image_id = builder.build_image(
            dockerfile_path="Dockerfile",
            build_context=".",
            tag="test:latest",
            build_args={"ARG1": "value1"},
        )

        assert image_id == "test:latest"
        mock_client.images.build.assert_called_once_with(
            path=".",
            dockerfile="Dockerfile",
            tag="test:latest",
            buildargs={"ARG1": "value1"},
            rm=True,
        )

    @patch("variousplug.base.Path")
    @patch("docker.from_env")
    def test_build_image_failure(self, mock_docker, mock_path):
        """Test Docker image build failure."""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        mock_client.images.build.side_effect = docker.errors.BuildError("Build failed", [])

        # Mock Path.exists to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        builder = DockerBuilder()

        result = builder.build_image("Dockerfile", ".", "test:latest")
        assert result is None

    @patch("variousplug.base.Path")
    @patch("docker.from_env")
    def test_build_image_default_parameters(self, mock_docker, mock_path):
        """Test Docker image build with default parameters."""
        mock_client = Mock()
        mock_docker.return_value = mock_client

        mock_image = Mock()
        mock_image.id = "sha256:efgh5678"
        mock_client.images.build.return_value = (mock_image, [])

        # Mock Path.exists to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        builder = DockerBuilder()
        image_id = builder.build_image("Dockerfile", ".", "test:latest")

        assert image_id == "test:latest"
        mock_client.images.build.assert_called_once_with(
            path=".", dockerfile="Dockerfile", tag="test:latest", buildargs={}, rm=True
        )

    @patch("docker.from_env")
    def test_docker_connection_error(self, mock_docker):
        """Test Docker connection error handling."""
        mock_docker.side_effect = docker.errors.DockerException("Cannot connect to Docker")

        builder = DockerBuilder()

        with pytest.raises(docker.errors.DockerException):
            builder._get_docker_client()
