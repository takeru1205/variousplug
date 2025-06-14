"""
Unit tests for VastFileSync implementation.
"""

from unittest.mock import Mock, patch

from variousplug.base import VastFileSync
from variousplug.interfaces import InstanceInfo, InstanceStatus


class TestVastFileSync:
    """Test VastFileSync implementation."""

    def test_vast_file_sync_init(self):
        """Test VastFileSync initialization."""
        sync = VastFileSync("test_api_key")
        assert sync.api_key == "test_api_key"

    @patch("subprocess.run")
    def test_upload_files_success(self, mock_subprocess):
        """Test successful file upload using rsync."""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root"
        )

        result = sync.upload_files(instance_info, "/local/path", "/workspace", ["*.pyc"])

        assert result is True
        # Verify rsync was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # First argument (command list)
        assert "rsync" in call_args[0]
        assert "/local/path/" in call_args
        assert "root@test.host:/workspace/" in call_args

    @patch("subprocess.run")
    def test_upload_files_failure(self, mock_subprocess):
        """Test failed file upload."""
        # Mock failed subprocess call
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "rsync error"
        mock_subprocess.return_value = mock_result

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root"
        )

        result = sync.upload_files(instance_info, "/local/path", "/workspace", [])

        assert result is False

    def test_upload_files_missing_ssh_info(self):
        """Test upload with missing SSH connection info."""
        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host=None,  # Missing SSH info
            ssh_port=None
        )

        result = sync.upload_files(instance_info, "/local/path", "/workspace", [])

        assert result is False

    @patch("subprocess.run")
    def test_upload_files_exception(self, mock_subprocess):
        """Test upload with exception."""
        mock_subprocess.side_effect = Exception("Subprocess error")

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root"
        )

        result = sync.upload_files(instance_info, "/local/path", "/workspace", [])

        assert result is False

    @patch("subprocess.run")
    @patch("variousplug.base.Path")
    def test_download_files_success(self, mock_path, mock_subprocess):
        """Test successful file download using rsync."""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root"
        )

        result = sync.download_files(
            instance_info=instance_info, remote_path="/workspace/data", local_path="./data"
        )

        assert result is True
        # Verify rsync was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # First argument (command list)
        assert "rsync" in call_args[0]
        assert "root@test.host:/workspace/data/" in call_args
        assert "./data/" in call_args
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("subprocess.run")
    @patch("variousplug.base.Path")
    def test_download_files_failure(self, mock_path, mock_subprocess):
        """Test failed file download."""
        # Mock failed subprocess call
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "rsync error"
        mock_subprocess.return_value = mock_result

        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root"
        )

        result = sync.download_files(
            instance_info=instance_info, remote_path="/workspace/data", local_path="./data"
        )

        assert result is False

    def test_download_files_missing_ssh_info(self):
        """Test download with missing SSH connection info."""
        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host=None,  # Missing SSH info
            ssh_port=None
        )

        result = sync.download_files(
            instance_info=instance_info, remote_path="/workspace/data", local_path="./data"
        )

        assert result is False

    @patch("subprocess.run")
    def test_download_files_exception(self, mock_subprocess):
        """Test download with exception."""
        mock_subprocess.side_effect = Exception("Subprocess error")

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING,
            ssh_host="test.host",
            ssh_port=22,
            ssh_username="root"
        )

        result = sync.download_files(
            instance_info=instance_info, remote_path="/workspace/data", local_path="./data"
        )

        assert result is False
