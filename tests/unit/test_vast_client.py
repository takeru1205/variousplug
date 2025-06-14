"""
Unit tests for Vast.ai client.
"""
from unittest.mock import Mock, patch

import pytest

from variousplug.interfaces import CreateInstanceRequest, InstanceStatus
from variousplug.vast_client import VastClient


class TestVastClient:
    """Test VastClient implementation."""

    def test_vast_client_init(self):
        """Test VastClient initialization."""
        client = VastClient("test_api_key")

        assert client.api_key == "test_api_key"
        assert client.platform_name == "vast"
        assert client._client is None

    @patch("variousplug.vast_client.VastAI")
    def test_create_client(self, mock_vast_ai):
        """Test _create_client method."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        client = VastClient("test_api_key")
        sdk_client = client._create_client()

        assert sdk_client == mock_sdk
        mock_vast_ai.assert_called_once_with(api_key="test_api_key")

    @patch("variousplug.vast_client.VastAI")
    def test_list_instances_success(self, mock_vast_ai):
        """Test successful instance listing."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        mock_instances = [
            {
                "id": 12345,
                "actual_status": "running",
                "gpu_name": "GTX_1080",
                "image": "pytorch/pytorch",
                "ssh_host": "ssh1.vast.ai",
                "ssh_port": 12345
            },
            {
                "id": 67890,
                "actual_status": "pending",
                "gpu_name": "RTX_3070",
                "image": "tensorflow/tensorflow",
                "ssh_host": None,
                "ssh_port": None
            }
        ]
        mock_sdk.show_instances.return_value = mock_instances

        client = VastClient("test_api_key")
        instances = client.list_instances()

        assert len(instances) == 2

        # Check first instance
        assert instances[0].id == "12345"
        assert instances[0].platform == "vast"
        assert instances[0].status == InstanceStatus.RUNNING
        assert instances[0].gpu_type == "GTX_1080"
        assert instances[0].image == "pytorch/pytorch"
        assert instances[0].ssh_host == "ssh1.vast.ai"
        assert instances[0].ssh_port == 12345

        # Check second instance
        assert instances[1].id == "67890"
        assert instances[1].status == InstanceStatus.PENDING

    @patch("variousplug.vast_client.VastAI")
    def test_list_instances_failure(self, mock_vast_ai):
        """Test instance listing failure."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.show_instances.side_effect = Exception("API Error")

        client = VastClient("test_api_key")

        with pytest.raises(Exception, match="API Error"):
            client.list_instances()

    @patch("variousplug.vast_client.VastAI")
    def test_get_instance_found(self, mock_vast_ai):
        """Test getting existing instance."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        mock_instances = [
            {
                "id": 12345,
                "actual_status": "running",
                "gpu_name": "GTX_1080",
                "image": "pytorch/pytorch"
            }
        ]
        mock_sdk.show_instances.return_value = mock_instances

        client = VastClient("test_api_key")
        instance = client.get_instance("12345")

        assert instance is not None
        assert instance.id == "12345"
        assert instance.platform == "vast"
        assert instance.status == InstanceStatus.RUNNING

    @patch("variousplug.vast_client.VastAI")
    def test_get_instance_not_found(self, mock_vast_ai):
        """Test getting non-existent instance."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.show_instances.return_value = []

        client = VastClient("test_api_key")
        instance = client.get_instance("nonexistent")

        assert instance is None

    @patch("variousplug.vast_client.VastAI")
    def test_get_instance_error(self, mock_vast_ai):
        """Test getting instance with API error."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.show_instances.side_effect = Exception("API Error")

        client = VastClient("test_api_key")
        instance = client.get_instance("12345")

        assert instance is None

    @patch("variousplug.vast_client.VastAI")
    def test_create_instance_success(self, mock_vast_ai):
        """Test successful instance creation."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.launch_instance.return_value = {"new_contract": 12345}

        client = VastClient("test_api_key")
        request = CreateInstanceRequest(
            gpu_type="GTX_1080",
            image="pytorch/pytorch"
        )

        instance = client.create_instance(request)

        assert instance.id == "12345"
        assert instance.platform == "vast"
        assert instance.status == InstanceStatus.PENDING

        # Check launch_instance was called with cost-optimized parameters
        mock_sdk.launch_instance.assert_called_once()
        call_kwargs = mock_sdk.launch_instance.call_args[1]
        assert call_kwargs["gpu_name"] == "GTX_1080"
        assert call_kwargs["image"] == "pytorch/pytorch"
        assert call_kwargs["price"] == "0.50"  # Cost optimization
        assert call_kwargs["disk_gb"] == "10"  # Cost optimization
        assert call_kwargs["direct_port_count"] == "1"  # Cost optimization

    @patch("variousplug.vast_client.VastAI")
    def test_create_instance_default_params(self, mock_vast_ai):
        """Test instance creation with default parameters."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.launch_instance.return_value = {"new_contract": 67890}

        client = VastClient("test_api_key")
        request = CreateInstanceRequest()  # No parameters

        instance = client.create_instance(request)

        # Check default values were used
        call_kwargs = mock_sdk.launch_instance.call_args[1]
        assert call_kwargs["gpu_name"] == "GTX_1070"  # Default cheap GPU
        assert call_kwargs["image"] == "pytorch/pytorch"  # Default image

    @patch("variousplug.vast_client.VastAI")
    def test_create_instance_failure(self, mock_vast_ai):
        """Test instance creation failure."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.launch_instance.side_effect = Exception("Launch failed")

        client = VastClient("test_api_key")
        request = CreateInstanceRequest()

        with pytest.raises(Exception, match="Launch failed"):
            client.create_instance(request)

    @patch("variousplug.vast_client.VastAI")
    def test_create_instance_unexpected_response(self, mock_vast_ai):
        """Test instance creation with unexpected response."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.launch_instance.return_value = {"error": "Something went wrong"}

        client = VastClient("test_api_key")
        request = CreateInstanceRequest()

        with pytest.raises(Exception, match="Unexpected response"):
            client.create_instance(request)

    @patch("variousplug.vast_client.VastAI")
    @patch("requests.delete")
    def test_destroy_instance_success_direct_api(self, mock_delete, mock_vast_ai):
        """Test successful instance destruction via direct API."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        # Make SDK methods fail to test direct API fallback
        mock_sdk.destroy_instance.side_effect = Exception("SDK Error")

        # Mock successful direct API call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        client = VastClient("test_api_key")
        result = client.destroy_instance("12345")

        assert result is True
        mock_delete.assert_called_once()

    @patch("variousplug.vast_client.VastAI")
    def test_destroy_instance_all_methods_fail(self, mock_vast_ai):
        """Test instance destruction when all methods fail."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.destroy_instance.side_effect = Exception("SDK Error")

        client = VastClient("test_api_key")

        with patch("requests.delete") as mock_delete:
            mock_delete.side_effect = Exception("Direct API Error")
            result = client.destroy_instance("12345")

        assert result is False

    @patch("variousplug.vast_client.VastAI")
    def test_execute_command_no_ssh(self, mock_vast_ai):
        """Test command execution without SSH (simulation mode)."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        # Mock instance without SSH
        mock_instances = [
            {
                "id": 12345,
                "actual_status": "running",
                "ssh_host": None,
                "ssh_port": None
            }
        ]
        mock_sdk.show_instances.return_value = mock_instances

        client = VastClient("test_api_key")
        result = client.execute_command("12345", ["python", "--version"])

        assert result.success is True
        assert "Python" in result.output

    @patch("variousplug.vast_client.VastAI")
    @patch("subprocess.run")
    def test_execute_command_ssh_success(self, mock_run, mock_vast_ai):
        """Test successful command execution via SSH."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        # Mock instance with SSH
        mock_instances = [
            {
                "id": 12345,
                "actual_status": "running",
                "ssh_host": "ssh1.vast.ai",
                "ssh_port": 12345
            }
        ]
        mock_sdk.show_instances.return_value = mock_instances

        # Mock successful SSH command
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Python 3.8.10"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        client = VastClient("test_api_key")
        result = client.execute_command("12345", ["python", "--version"])

        assert result.success is True
        assert result.output == "Python 3.8.10"
        assert result.return_code == 0

    @patch("variousplug.vast_client.VastAI")
    @patch("subprocess.run")
    def test_execute_command_ssh_failure(self, mock_run, mock_vast_ai):
        """Test command execution SSH failure with fallback."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        # Mock instance with SSH
        mock_instances = [
            {
                "id": 12345,
                "actual_status": "running",
                "ssh_host": "ssh1.vast.ai",
                "ssh_port": 12345
            }
        ]
        mock_sdk.show_instances.return_value = mock_instances

        # Mock failed SSH command
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Connection failed"
        mock_run.return_value = mock_process

        client = VastClient("test_api_key")
        result = client.execute_command("12345", ["python", "--version"])

        # Should fallback to simulation
        assert result.success is True
        assert "simulation" in result.output.lower()

    @patch("variousplug.vast_client.VastAI")
    def test_execute_command_instance_not_found(self, mock_vast_ai):
        """Test command execution on non-existent instance."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk
        mock_sdk.show_instances.return_value = []

        client = VastClient("test_api_key")
        result = client.execute_command("nonexistent", ["echo", "test"])

        assert result.success is False
        assert "not found" in result.error

    @patch("variousplug.vast_client.VastAI")
    def test_execute_command_instance_not_running(self, mock_vast_ai):
        """Test command execution on non-running instance."""
        mock_sdk = Mock()
        mock_vast_ai.return_value = mock_sdk

        # Mock stopped instance
        mock_instances = [
            {
                "id": 12345,
                "actual_status": "stopped"
            }
        ]
        mock_sdk.show_instances.return_value = mock_instances

        client = VastClient("test_api_key")
        result = client.execute_command("12345", ["echo", "test"])

        assert result.success is False
        assert "not running" in result.error

    def test_create_instance_info_full_data(self):
        """Test _create_instance_info with full data."""
        client = VastClient("test_api_key")

        raw_data = {
            "id": 12345,
            "actual_status": "running",
            "gpu_name": "GTX_1080",
            "image": "pytorch/pytorch",
            "ssh_host": "ssh1.vast.ai",
            "ssh_port": 12345,
            "gpuCount": 1,
            "vcpuCount": 4,
            "memoryInGb": 16
        }

        instance = client._create_instance_info(raw_data)

        assert instance.id == "12345"
        assert instance.platform == "vast"
        assert instance.status == InstanceStatus.RUNNING
        assert instance.gpu_type == "GTX_1080"
        assert instance.image == "pytorch/pytorch"
        assert instance.ssh_host == "ssh1.vast.ai"
        assert instance.ssh_port == 12345
        assert instance.ssh_username == "root"
        assert instance.raw_data == raw_data

    def test_create_instance_info_minimal_data(self):
        """Test _create_instance_info with minimal data."""
        client = VastClient("test_api_key")

        raw_data = {
            "id": 67890,
            "actual_status": None
        }

        instance = client._create_instance_info(raw_data)

        assert instance.id == "67890"
        assert instance.platform == "vast"
        assert instance.status == InstanceStatus.UNKNOWN
        assert instance.gpu_type is None
        assert instance.image is None
        assert instance.ssh_host is None
        assert instance.ssh_port is None

    def test_try_direct_api_destroy_success(self):
        """Test direct API destroy success."""
        client = VastClient("test_api_key")

        with patch("requests.delete") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            result = client._try_direct_api_destroy("12345")

            assert result == {"success": True}
            mock_delete.assert_called_once_with(
                "https://console.vast.ai/api/v0/instances/12345/",
                headers={
                    "Authorization": "Bearer test_api_key",
                    "Content-Type": "application/json"
                },
                timeout=30
            )

    def test_try_direct_api_destroy_failure(self):
        """Test direct API destroy failure."""
        client = VastClient("test_api_key")

        with patch("requests.delete") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_delete.return_value = mock_response

            with pytest.raises(Exception, match="HTTP 404: Not found"):
                client._try_direct_api_destroy("12345")

    def test_additional_params_handling(self):
        """Test handling of additional parameters in create_instance."""
        with patch("variousplug.vast_client.VastAI") as mock_vast_ai:
            mock_sdk = Mock()
            mock_vast_ai.return_value = mock_sdk
            mock_sdk.launch_instance.return_value = {"new_contract": 12345}

            client = VastClient("test_api_key")
            request = CreateInstanceRequest(
                additional_params={
                    "memory_gb": "32",
                    "price": "0.25",  # Should be capped at 0.50
                    "custom_param": "value"
                }
            )

            client.create_instance(request)

            call_kwargs = mock_sdk.launch_instance.call_args[1]
            assert call_kwargs["memory_gb"] == "32"
            assert call_kwargs["price"] == "0.25"  # Lower price allowed
            assert call_kwargs["custom_param"] == "value"
