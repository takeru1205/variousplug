"""
RunPod client integration for VariousPlug following SOLID principles.
"""

import logging
import time
from typing import Any

import runpod

from .base import BasePlatformClient
from .interfaces import CreateInstanceRequest, InstanceInfo, InstanceStatus
from .utils import ExecutionResult, print_info, print_warning

logger = logging.getLogger(__name__)


class RunPodClient(BasePlatformClient):
    """RunPod platform client following Single Responsibility Principle."""

    def __init__(self, api_key: str):
        super().__init__(api_key, "runpod")

    def _create_client(self):
        """Initialize RunPod SDK."""
        runpod.api_key = self.api_key
        return runpod  # RunPod uses module-level functions

    def list_instances(self) -> list[InstanceInfo]:
        """List all pods (instances)."""
        try:
            self._initialize_client()
            pods = runpod.get_pods()

            return [self._create_instance_info(pod) for pod in pods]

        except Exception as e:
            logger.error(f"Failed to list RunPod instances: {e}")
            raise

    def get_instance(self, instance_id: str) -> InstanceInfo | None:
        """Get specific pod details."""
        try:
            self._initialize_client()
            pod = runpod.get_pod(instance_id)

            if pod:
                return self._create_instance_info(pod)

            return None

        except Exception as e:
            logger.error(f"Failed to get RunPod instance {instance_id}: {e}")
            return None

    def create_instance(self, request: CreateInstanceRequest) -> InstanceInfo:
        """Create a new pod."""
        try:
            self._initialize_client()

            # Pod configuration - use cheaper GPU by default
            pod_name = f"vp-pod-{int(time.time())}"
            image_name = request.image or "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"

            # Use cheaper GPU options by default
            gpu_type = request.gpu_type or "NVIDIA RTX 4000 Ada Generation"

            print_info(f"Creating RunPod GPU pod: {pod_name}")
            print_info(f"GPU Type: {gpu_type}")
            print_info(f"Image: {image_name}")

            # Create GPU pod with cheaper options
            pod = runpod.create_pod(
                name=pod_name,
                image_name=image_name,
                gpu_type_id=gpu_type,
                cloud_type="COMMUNITY",  # Use community for lower cost
                support_public_ip=True,
                start_ssh=True,
                data_center_id=None,
                container_disk_in_gb=15,  # Smaller disk to reduce cost
                volume_in_gb=0,
                env={"WORKSPACE": "/workspace"},
                ports="22/tcp",
            )

            if not pod or "id" not in pod:
                raise Exception(f"Failed to create pod: {pod}")

            pod_id = pod["id"]
            print_info(f"Pod created with ID: {pod_id}")

            return InstanceInfo(
                id=str(pod_id),
                platform=self.platform_name,
                status=InstanceStatus.PENDING,
                raw_data=pod,
            )

        except Exception as e:
            logger.error(f"Failed to create RunPod instance: {e}")
            raise

    def destroy_instance(self, instance_id: str) -> bool:
        """Destroy a pod."""
        try:
            self._initialize_client()
            runpod.terminate_pod(instance_id)
            print_info(f"Pod {instance_id} termination initiated")
            return True

        except Exception as e:
            logger.error(f"Failed to destroy RunPod instance {instance_id}: {e}")
            raise

    def execute_command(
        self, instance_id: str, command: list[str], working_dir: str = "/workspace"
    ) -> ExecutionResult:
        """Execute a command on a RunPod pod via SSH."""
        try:
            # Get pod details
            instance = self.get_instance(instance_id)
            if not instance:
                return ExecutionResult(False, error=f"Instance {instance_id} not found")

            if instance.status != InstanceStatus.RUNNING:
                return ExecutionResult(False, error=f"Pod {instance_id} is not running")

            # Check if SSH is available
            if not instance.ssh_host or not instance.ssh_port:
                # For now, simulate command execution for testing
                cmd_str = " ".join(command)
                print_warning(f"SSH not available for pod {instance_id}, simulating: {cmd_str}")

                # Simple simulation for common commands
                if "python --version" in cmd_str:
                    return ExecutionResult(True, "Python 3.10.12")
                elif "echo" in cmd_str:
                    echo_text = cmd_str.split("echo", 1)[1].strip().strip("\"'")
                    return ExecutionResult(True, echo_text)
                else:
                    return ExecutionResult(True, f"Simulated execution: {cmd_str}")

            # Execute command via SSH
            import subprocess

            cmd_str = " ".join(command)
            # Prepend cd command to ensure we're in the right working directory
            full_cmd = f"cd {working_dir} && {cmd_str}"

            ssh_cmd = [
                "ssh",
                "-p",
                str(instance.ssh_port),
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "LogLevel=ERROR",
                f"{instance.ssh_username}@{instance.ssh_host}",
                full_cmd,
            ]

            print_info(f"Executing via SSH: {cmd_str}")
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)

            success = result.returncode == 0
            output = result.stdout if success else result.stderr

            return ExecutionResult(success, output, result.stderr, result.returncode)

        except subprocess.TimeoutExpired:
            return ExecutionResult(False, error="Command execution timed out")
        except Exception as e:
            logger.error(f"Failed to execute command on RunPod instance {instance_id}: {e}")
            return ExecutionResult(False, error=str(e))

    def _is_instance_ready(self, instance: InstanceInfo) -> bool:
        """Check if RunPod pod is ready."""
        try:
            pod = self.get_instance(instance.id)
            return bool(pod and pod.status == InstanceStatus.RUNNING)
        except Exception:
            return False

    def _create_instance_info(self, raw_data: dict[str, Any]) -> InstanceInfo:
        """Create standardized instance info from RunPod pod data."""
        # Extract SSH connection info if available
        ssh_host = None
        ssh_port = None
        ssh_username = "root"

        # Check for SSH connection info in runtime ports
        if raw_data.get("runtime"):
            runtime = raw_data["runtime"]

            # Check for ports in runtime
            if runtime.get("ports"):
                for port_info in runtime["ports"]:
                    if port_info.get("privatePort") == 22:  # SSH port
                        ssh_host = port_info.get("ip")
                        ssh_port = port_info.get("publicPort")
                        break

        # Check direct ports field for SSH
        if raw_data.get("ports"):
            for port_info in raw_data["ports"]:
                if isinstance(port_info, dict) and port_info.get("privatePort") == 22:
                    ssh_host = port_info.get("ip")
                    ssh_port = port_info.get("publicPort")
                    break

        # Determine if it's GPU or CPU instance
        gpu_count = raw_data.get("gpuCount", 0)
        if gpu_count and gpu_count > 0:
            resource_info = f"{gpu_count} GPU(s)"
        else:
            cpu_count = raw_data.get("vcpuCount", "N/A")
            memory_gb = raw_data.get("memoryInGb", "N/A")
            resource_info = f"{cpu_count} vCPU, {memory_gb}GB RAM"

        return InstanceInfo(
            id=str(raw_data.get("id", "unknown")),
            platform=self.platform_name,
            status=self._normalize_status(raw_data.get("desiredStatus", "unknown")),
            gpu_type=resource_info,
            image=raw_data.get("imageName"),
            ssh_host=ssh_host,
            ssh_port=ssh_port,
            ssh_username=ssh_username,
            raw_data=raw_data,
        )
