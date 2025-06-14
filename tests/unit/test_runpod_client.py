"""
Unit tests for RunPod client.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest

from variousplug.interfaces import CreateInstanceRequest, InstanceInfo, InstanceStatus
from variousplug.runpod_client import RunPodClient


class TestRunPodClient:
    """Test RunPodClient implementation."""

    def test_runpod_client_init(self):
        """Test RunPodClient initialization."""
        client = RunPodClient("test_api_key")

        assert client.api_key == "test_api_key"
        assert client.platform_name == "runpod"
        assert client._client is None

    @patch("variousplug.runpod_client.runpod")
    def test_create_client(self, mock_runpod):
        """Test _create_client method."""
        client = RunPodClient("test_api_key")
        sdk_client = client._create_client()

        assert sdk_client == mock_runpod
        assert mock_runpod.api_key == "test_api_key"

    @patch("variousplug.runpod_client.runpod")
    def test_list_instances_success(self, mock_runpod):
        """Test successful instance listing."""
        mock_pods = [
            {
                "id": "pod_123",
                "desiredStatus": "RUNNING",
                "imageName": "runpod/pytorch:latest",
                "gpuCount": 1,
                "runtime": {
                    "ports": [{"privatePort": 22, "ip": "pod.runpod.io", "publicPort": 12345}]
                },
            },
            {
                "id": "pod_456",
                "desiredStatus": "PENDING",
                "imageName": "runpod/tensorflow:latest",
                "gpuCount": 1,
            },
        ]
        mock_runpod.get_pods.return_value = mock_pods

        client = RunPodClient("test_api_key")
        instances = client.list_instances()

        assert len(instances) == 2

        # Check first instance
        assert instances[0].id == "pod_123"
        assert instances[0].platform == "runpod"
        assert instances[0].status == InstanceStatus.RUNNING
        assert instances[0].image == "runpod/pytorch:latest"
        assert instances[0].ssh_host == "pod.runpod.io"
        assert instances[0].ssh_port == 12345

        # Check second instance
        assert instances[1].id == "pod_456"
        assert instances[1].status == InstanceStatus.PENDING

    @patch("variousplug.runpod_client.runpod")
    def test_list_instances_failure(self, mock_runpod):
        """Test instance listing failure."""
        mock_runpod.get_pods.side_effect = Exception("API Error")

        client = RunPodClient("test_api_key")

        with pytest.raises(Exception, match="API Error"):
            client.list_instances()

    @patch("variousplug.runpod_client.runpod")
    def test_get_instance_found(self, mock_runpod):
        """Test getting existing instance."""
        mock_pod = {
            "id": "pod_123",
            "desiredStatus": "RUNNING",
            "imageName": "runpod/pytorch:latest",
            "gpuCount": 1,
        }
        mock_runpod.get_pod.return_value = mock_pod

        client = RunPodClient("test_api_key")
        instance = client.get_instance("pod_123")

        assert instance is not None
        assert instance.id == "pod_123"
        assert instance.platform == "runpod"
        assert instance.status == InstanceStatus.RUNNING

    @patch("variousplug.runpod_client.runpod")
    def test_get_instance_not_found(self, mock_runpod):
        """Test getting non-existent instance."""
        mock_runpod.get_pod.return_value = None

        client = RunPodClient("test_api_key")
        instance = client.get_instance("nonexistent")

        assert instance is None

    @patch("variousplug.runpod_client.runpod")
    def test_get_instance_error(self, mock_runpod):
        """Test getting instance with API error."""
        mock_runpod.get_pod.side_effect = Exception("API Error")

        client = RunPodClient("test_api_key")
        instance = client.get_instance("pod_123")

        assert instance is None

    @patch("variousplug.runpod_client.runpod")
    @patch("time.time")
    def test_create_instance_success(self, mock_time, mock_runpod):
        """Test successful instance creation."""
        mock_time.return_value = 1234567890
        mock_runpod.create_pod.return_value = {"id": "pod_new_123"}

        client = RunPodClient("test_api_key")
        request = CreateInstanceRequest(gpu_type="NVIDIA RTX 4090", image="runpod/pytorch:latest")

        instance = client.create_instance(request)

        assert instance.id == "pod_new_123"
        assert instance.platform == "runpod"
        assert instance.status == InstanceStatus.PENDING

        # Check create_pod was called with cost-optimized parameters
        mock_runpod.create_pod.assert_called_once()
        call_kwargs = mock_runpod.create_pod.call_args[1]
        assert call_kwargs["name"] == "vp-pod-1234567890"
        assert call_kwargs["image_name"] == "runpod/pytorch:latest"
        assert call_kwargs["gpu_type_id"] == "NVIDIA RTX 4090"
        assert call_kwargs["cloud_type"] == "COMMUNITY"  # Cost optimization
        assert call_kwargs["container_disk_in_gb"] == 15  # Cost optimization
        assert call_kwargs["volume_in_gb"] == 0  # Cost optimization

    @patch("variousplug.runpod_client.runpod")
    @patch("time.time")
    def test_create_instance_default_params(self, mock_time, mock_runpod):
        """Test instance creation with default parameters."""
        mock_time.return_value = 1234567890
        mock_runpod.create_pod.return_value = {"id": "pod_default_123"}

        client = RunPodClient("test_api_key")
        request = CreateInstanceRequest()  # No parameters

        client.create_instance(request)

        # Check default values were used
        call_kwargs = mock_runpod.create_pod.call_args[1]
        assert call_kwargs["gpu_type_id"] == "NVIDIA RTX 4000 Ada Generation"  # Default
        assert (
            call_kwargs["image_name"] == "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
        )  # Default

    @patch("variousplug.runpod_client.runpod")
    def test_create_instance_failure(self, mock_runpod):
        """Test instance creation failure."""
        mock_runpod.create_pod.side_effect = Exception("Pod creation failed")

        client = RunPodClient("test_api_key")
        request = CreateInstanceRequest()

        with pytest.raises(Exception, match="Pod creation failed"):
            client.create_instance(request)

    @patch("variousplug.runpod_client.runpod")
    def test_create_instance_invalid_response(self, mock_runpod):
        """Test instance creation with invalid response."""
        mock_runpod.create_pod.return_value = None

        client = RunPodClient("test_api_key")
        request = CreateInstanceRequest()

        with pytest.raises(Exception, match="Failed to create pod"):
            client.create_instance(request)

    @patch("variousplug.runpod_client.runpod")
    def test_destroy_instance_success(self, mock_runpod):
        """Test successful instance destruction."""
        mock_runpod.terminate_pod.return_value = True

        client = RunPodClient("test_api_key")
        result = client.destroy_instance("pod_123")

        assert result is True
        mock_runpod.terminate_pod.assert_called_once_with("pod_123")

    @patch("variousplug.runpod_client.runpod")
    def test_destroy_instance_failure(self, mock_runpod):
        """Test instance destruction failure."""
        mock_runpod.terminate_pod.side_effect = Exception("Termination failed")

        client = RunPodClient("test_api_key")

        with pytest.raises(Exception, match="Termination failed"):
            client.destroy_instance("pod_123")

    @patch("variousplug.runpod_client.runpod")
    def test_execute_command_no_ssh(self, mock_runpod):
        """Test command execution without SSH (simulation mode)."""
        mock_pod = {"id": "pod_123", "desiredStatus": "RUNNING"}
        mock_runpod.get_pod.return_value = mock_pod

        client = RunPodClient("test_api_key")
        result = client.execute_command("pod_123", ["python", "--version"])

        assert result.success is True
        assert "Python" in result.output

    @patch("variousplug.runpod_client.runpod")
    @patch("subprocess.run")
    def test_execute_command_ssh_success(self, mock_run, mock_runpod):
        """Test successful command execution via SSH."""
        mock_pod = {
            "id": "pod_123",
            "desiredStatus": "RUNNING",
            "runtime": {"ports": [{"privatePort": 22, "ip": "pod.runpod.io", "publicPort": 12345}]},
        }
        mock_runpod.get_pod.return_value = mock_pod

        # Mock successful SSH command
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Python 3.10.12"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = RunPodClient("test_api_key")
        result = client.execute_command("pod_123", ["python", "--version"])

        assert result.success is True
        assert result.output == "Python 3.10.12"
        assert result.exit_code == 0

    @patch("variousplug.runpod_client.runpod")
    def test_execute_command_instance_not_found(self, mock_runpod):
        """Test command execution on non-existent instance."""
        mock_runpod.get_pod.return_value = None

        client = RunPodClient("test_api_key")
        result = client.execute_command("nonexistent", ["echo", "test"])

        assert result.success is False
        assert "not found" in result.error

    @patch("variousplug.runpod_client.runpod")
    def test_execute_command_instance_not_running(self, mock_runpod):
        """Test command execution on non-running instance."""
        mock_pod = {"id": "pod_123", "desiredStatus": "STOPPED"}
        mock_runpod.get_pod.return_value = mock_pod

        client = RunPodClient("test_api_key")
        result = client.execute_command("pod_123", ["echo", "test"])

        assert result.success is False
        assert "not running" in result.error

    def test_create_instance_info_with_ssh(self):
        """Test _create_instance_info with SSH information."""
        client = RunPodClient("test_api_key")

        raw_data = {
            "id": "pod_123",
            "desiredStatus": "RUNNING",
            "imageName": "runpod/pytorch:latest",
            "gpuCount": 2,
            "runtime": {"ports": [{"privatePort": 22, "ip": "pod.runpod.io", "publicPort": 12345}]},
        }

        instance = client._create_instance_info(raw_data)

        assert instance.id == "pod_123"
        assert instance.platform == "runpod"
        assert instance.status == InstanceStatus.RUNNING
        assert instance.image == "runpod/pytorch:latest"
        assert instance.gpu_type == "2 GPU(s)"
        assert instance.ssh_host == "pod.runpod.io"
        assert instance.ssh_port == 12345
        assert instance.ssh_username == "root"

    def test_create_instance_info_without_ssh(self):
        """Test _create_instance_info without SSH information."""
        client = RunPodClient("test_api_key")

        raw_data = {
            "id": "pod_456",
            "desiredStatus": "PENDING",
            "imageName": "runpod/tensorflow:latest",
            "vcpuCount": 4,
            "memoryInGb": 16,
        }

        instance = client._create_instance_info(raw_data)

        assert instance.id == "pod_456"
        assert instance.platform == "runpod"
        assert instance.status == InstanceStatus.PENDING
        assert instance.image == "runpod/tensorflow:latest"
        assert instance.gpu_type == "4 vCPU, 16GB RAM"
        assert instance.ssh_host is None
        assert instance.ssh_port is None

    def test_create_instance_info_ports_field(self):
        """Test _create_instance_info with ports in direct field."""
        client = RunPodClient("test_api_key")

        raw_data = {
            "id": "pod_789",
            "desiredStatus": "RUNNING",
            "ports": [{"privatePort": 22, "ip": "direct.runpod.io", "publicPort": 54321}],
        }

        instance = client._create_instance_info(raw_data)

        assert instance.ssh_host == "direct.runpod.io"
        assert instance.ssh_port == 54321

    @patch("variousplug.runpod_client.runpod")
    def test_is_instance_ready(self, mock_runpod):
        """Test _is_instance_ready method."""
        # Mock get_instance to return running instance
        mock_pod = {"id": "pod_123", "desiredStatus": "RUNNING"}
        mock_runpod.get_pod.return_value = mock_pod

        client = RunPodClient("test_api_key")
        instance = InstanceInfo(id="pod_123", platform="runpod", status=InstanceStatus.PENDING)

        result = client._is_instance_ready(instance)
        assert result is True

    @patch("variousplug.runpod_client.runpod")
    def test_is_instance_ready_failure(self, mock_runpod):
        """Test _is_instance_ready method with failure."""
        mock_runpod.get_pod.side_effect = Exception("API Error")

        client = RunPodClient("test_api_key")
        instance = InstanceInfo(id="pod_123", platform="runpod", status=InstanceStatus.PENDING)

        result = client._is_instance_ready(instance)
        assert result is False

    @patch("variousplug.runpod_client.runpod")
    @patch("subprocess.run")
    def test_execute_command_timeout(self, mock_run, mock_runpod):
        """Test command execution timeout."""
        mock_pod = {
            "id": "pod_123",
            "desiredStatus": "RUNNING",
            "runtime": {"ports": [{"privatePort": 22, "ip": "pod.runpod.io", "publicPort": 12345}]},
        }
        mock_runpod.get_pod.return_value = mock_pod

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 300)

        client = RunPodClient("test_api_key")
        result = client.execute_command("pod_123", ["sleep", "1000"])

        assert result.success is False
        assert "timed out" in result.error

    def test_create_instance_info_minimal_data(self):
        """Test _create_instance_info with minimal data."""
        client = RunPodClient("test_api_key")

        raw_data = {"id": "pod_minimal"}

        instance = client._create_instance_info(raw_data)

        assert instance.id == "pod_minimal"
        assert instance.platform == "runpod"
        assert instance.status == InstanceStatus.UNKNOWN
        assert instance.image is None
        assert instance.gpu_type == "N/A vCPU, N/AGB RAM"  # Default for CPU instance
