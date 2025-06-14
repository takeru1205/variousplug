"""
Factory classes implementing the Abstract Factory pattern for platform creation.
"""

from typing import Any

from .base import RsyncFileSync, VastFileSync
from .interfaces import IFileSync, IPlatformClient, IPlatformFactory
from .runpod_client import RunPodClient
from .vast_client import VastClient


class PlatformFactory(IPlatformFactory):
    """Factory for creating platform clients (Open/Closed Principle)."""

    def __init__(self):
        self._platform_creators = {
            "vast": self._create_vast_client,
            "runpod": self._create_runpod_client,
        }

        self._file_sync_creators = {
            "vast": self._create_vast_file_sync,
            "runpod": lambda _config: RsyncFileSync(),  # RunPod pods now support SSH
        }

    def create_client(self, platform: str, config: dict[str, Any]) -> IPlatformClient:
        """Create platform client based on platform type."""
        if platform not in self._platform_creators:
            raise ValueError(f"Unsupported platform: {platform}")

        api_key = config.get("api_key")
        if not api_key:
            raise ValueError(f"API key not configured for platform: {platform}")

        return self._platform_creators[platform](api_key)

    def create_file_sync(self, platform: str, config: dict[str, Any] | None = None) -> IFileSync:
        """Create file sync client for platform."""
        if platform not in self._file_sync_creators:
            raise ValueError(f"Unsupported platform: {platform}")

        return self._file_sync_creators[platform](config)

    def get_supported_platforms(self) -> list[str]:
        """Get list of supported platforms."""
        return list(self._platform_creators.keys())

    def register_platform(self, platform: str, client_creator, file_sync_creator):
        """Register a new platform (Open/Closed Principle)."""
        self._platform_creators[platform] = client_creator
        self._file_sync_creators[platform] = file_sync_creator

    def _create_vast_client(self, api_key: str) -> IPlatformClient:
        """Create Vast.ai client."""
        return VastClient(api_key)

    def _create_runpod_client(self, api_key: str) -> IPlatformClient:
        """Create RunPod client."""
        return RunPodClient(api_key)

    def _create_vast_file_sync(self, config: dict[str, Any] | None = None) -> IFileSync:
        """Create Vast.ai file sync client."""
        if not config or not config.get("api_key"):
            raise ValueError("API key required for Vast.ai file sync")

        return VastFileSync(config["api_key"])
