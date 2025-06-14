"""
Unit tests for VastFileSync implementation.
"""
from unittest.mock import Mock, patch
from pathlib import Path

import pytest

from variousplug.base import VastFileSync
from variousplug.interfaces import InstanceInfo, InstanceStatus


class TestVastFileSync:
    """Test VastFileSync implementation."""

    def test_vast_file_sync_init(self):
        """Test VastFileSync initialization."""
        sync = VastFileSync("test_api_key")
        assert sync.api_key == "test_api_key"
        assert sync._client is None

    @patch("vastai_sdk.VastAI")
    def test_initialize_client(self, mock_vast_ai):
        """Test client initialization."""
        mock_client = Mock()
        mock_vast_ai.return_value = mock_client

        sync = VastFileSync("test_api_key")
        sync._initialize_client()

        assert sync._client == mock_client
        mock_vast_ai.assert_called_once_with(api_key="test_api_key")

    @patch("vastai_sdk.VastAI")
    def test_upload_files_success(self, mock_vast_ai):
        """Test successful file upload."""
        mock_client = Mock()
        mock_client.copy.return_value = 0
        mock_vast_ai.return_value = mock_client

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/workspace",
            exclude_patterns=["*.pyc"]
        )

        assert result is True
        mock_client.copy.assert_called_once_with(
            src="/local/path/",
            dst="test-instance:/workspace/"
        )

    @patch("vastai_sdk.VastAI")
    def test_upload_files_failure(self, mock_vast_ai):
        """Test failed file upload."""
        mock_client = Mock()
        mock_client.copy.return_value = 1  # Non-zero return indicates failure
        mock_vast_ai.return_value = mock_client

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/workspace",
            exclude_patterns=[]
        )

        assert result is False

    @patch("vastai_sdk.VastAI")
    def test_upload_files_missing_instance_id(self, mock_vast_ai):
        """Test upload with missing instance ID."""
        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/workspace",
            exclude_patterns=[]
        )

        assert result is False

    @patch("vastai_sdk.VastAI")
    def test_upload_files_exception(self, mock_vast_ai):
        """Test upload with exception."""
        mock_client = Mock()
        mock_client.copy.side_effect = Exception("API error")
        mock_vast_ai.return_value = mock_client

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.upload_files(
            instance_info=instance_info,
            local_path="/local/path",
            remote_path="/workspace",
            exclude_patterns=[]
        )

        assert result is False

    @patch("vastai_sdk.VastAI")
    @patch("variousplug.base.Path")
    def test_download_files_success(self, mock_path, mock_vast_ai):
        """Test successful file download."""
        mock_client = Mock()
        mock_client.copy.return_value = 0
        mock_vast_ai.return_value = mock_client
        
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.download_files(
            instance_info=instance_info,
            remote_path="/workspace/data",
            local_path="./data"
        )

        assert result is True
        mock_client.copy.assert_called_once_with(
            src="test-instance:/workspace/data/",
            dst="./data/"
        )
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("vastai_sdk.VastAI")
    @patch("variousplug.base.Path")
    def test_download_files_with_warnings(self, mock_path, mock_vast_ai):
        """Test download with warnings (should still return True)."""
        mock_client = Mock()
        mock_client.copy.return_value = 1  # Non-zero but not failure
        mock_vast_ai.return_value = mock_client
        
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.download_files(
            instance_info=instance_info,
            remote_path="/workspace/data",
            local_path="./data"
        )

        assert result is True  # Should return True even with warnings

    @patch("vastai_sdk.VastAI")
    def test_download_files_missing_instance_id(self, mock_vast_ai):
        """Test download with missing instance ID."""
        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.download_files(
            instance_info=instance_info,
            remote_path="/workspace/data",
            local_path="./data"
        )

        assert result is False

    @patch("vastai_sdk.VastAI")
    def test_download_files_exception(self, mock_vast_ai):
        """Test download with exception."""
        mock_client = Mock()
        mock_client.copy.side_effect = Exception("API error")
        mock_vast_ai.return_value = mock_client

        sync = VastFileSync("test_api_key")
        instance_info = InstanceInfo(
            id="test-instance",
            platform="vast",
            status=InstanceStatus.RUNNING
        )

        result = sync.download_files(
            instance_info=instance_info,
            remote_path="/workspace/data",
            local_path="./data"
        )

        assert result is False