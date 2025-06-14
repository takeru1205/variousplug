"""
Unit tests for VariousPlug factory pattern implementation.
"""

from unittest.mock import Mock, patch

import pytest

from variousplug.factory import PlatformFactory


class TestPlatformFactory:
    """Test PlatformFactory implementation."""

    def test_platform_factory_init(self):
        """Test PlatformFactory initialization."""
        factory = PlatformFactory()

        assert factory is not None
        assert "vast" in factory._platform_creators
        assert "runpod" in factory._platform_creators
        assert "vast" in factory._file_sync_creators
        assert "runpod" in factory._file_sync_creators

    def test_get_supported_platforms(self):
        """Test getting supported platforms."""
        factory = PlatformFactory()
        platforms = factory.get_supported_platforms()

        assert isinstance(platforms, list)
        assert "vast" in platforms
        assert "runpod" in platforms
        assert len(platforms) == 2

    @patch("variousplug.factory.VastClient")
    def test_create_vast_client(self, mock_vast_client):
        """Test creating Vast.ai client."""
        mock_client_instance = Mock()
        mock_vast_client.return_value = mock_client_instance

        factory = PlatformFactory()
        config = {"api_key": "test_vast_key"}

        client = factory.create_client("vast", config)

        assert client == mock_client_instance
        mock_vast_client.assert_called_once_with("test_vast_key")

    @patch("variousplug.factory.RunPodClient")
    def test_create_runpod_client(self, mock_runpod_client):
        """Test creating RunPod client."""
        mock_client_instance = Mock()
        mock_runpod_client.return_value = mock_client_instance

        factory = PlatformFactory()
        config = {"api_key": "test_runpod_key"}

        client = factory.create_client("runpod", config)

        assert client == mock_client_instance
        mock_runpod_client.assert_called_once_with("test_runpod_key")

    def test_create_client_unsupported_platform(self):
        """Test creating client for unsupported platform."""
        factory = PlatformFactory()
        config = {"api_key": "test_key"}

        with pytest.raises(ValueError, match="Unsupported platform: unknown"):
            factory.create_client("unknown", config)

    def test_create_client_missing_api_key(self):
        """Test creating client with missing API key."""
        factory = PlatformFactory()
        config = {}  # No api_key

        with pytest.raises(ValueError, match="API key not configured for platform: vast"):
            factory.create_client("vast", config)

    def test_create_client_none_api_key(self):
        """Test creating client with None API key."""
        factory = PlatformFactory()
        config = {"api_key": None}

        with pytest.raises(ValueError, match="API key not configured for platform: vast"):
            factory.create_client("vast", config)

    @patch("variousplug.factory.VastFileSync")
    def test_create_vast_file_sync(self, mock_vast_sync):
        """Test creating Vast.ai file sync."""
        mock_sync_instance = Mock()
        mock_vast_sync.return_value = mock_sync_instance

        factory = PlatformFactory()
        config = {"api_key": "test_key"}
        sync = factory.create_file_sync("vast", config)

        assert sync == mock_sync_instance
        mock_vast_sync.assert_called_once_with("test_key")

    def test_create_vast_file_sync_missing_api_key(self):
        """Test creating Vast.ai file sync without API key."""
        factory = PlatformFactory()

        with pytest.raises(ValueError, match="API key required for Vast.ai file sync"):
            factory.create_file_sync("vast", {})

    @patch("variousplug.factory.RsyncFileSync")
    def test_create_runpod_file_sync(self, mock_rsync):
        """Test creating RunPod file sync."""
        mock_sync_instance = Mock()
        mock_rsync.return_value = mock_sync_instance

        factory = PlatformFactory()
        sync = factory.create_file_sync("runpod", {})

        assert sync == mock_sync_instance
        mock_rsync.assert_called_once()

    def test_create_file_sync_unsupported_platform(self):
        """Test creating file sync for unsupported platform."""
        factory = PlatformFactory()

        with pytest.raises(ValueError, match="Unsupported platform: unknown"):
            factory.create_file_sync("unknown", {})

    def test_register_platform(self):
        """Test registering a new platform."""
        factory = PlatformFactory()

        # Mock client and file sync creators
        mock_client_creator = Mock()
        mock_file_sync_creator = Mock()

        # Register new platform
        factory.register_platform("aws", mock_client_creator, mock_file_sync_creator)

        # Verify platform was registered
        platforms = factory.get_supported_platforms()
        assert "aws" in platforms
        assert len(platforms) == 3

        # Test creating client for new platform
        config = {"api_key": "aws_key"}
        factory.create_client("aws", config)
        mock_client_creator.assert_called_once_with("aws_key")

        # Test creating file sync for new platform
        factory.create_file_sync("aws", {})
        mock_file_sync_creator.assert_called_once()

    def test_factory_extensibility(self):
        """Test factory pattern supports extensibility (Open/Closed Principle)."""
        factory = PlatformFactory()
        original_platforms = set(factory.get_supported_platforms())

        # Add multiple new platforms
        factory.register_platform("azure", Mock(), Mock())
        factory.register_platform("gcp", Mock(), Mock())

        new_platforms = set(factory.get_supported_platforms())

        # Original platforms should still be there
        assert original_platforms.issubset(new_platforms)

        # New platforms should be added
        assert "azure" in new_platforms
        assert "gcp" in new_platforms
        assert len(new_platforms) == len(original_platforms) + 2

    def test_create_client_with_empty_string_api_key(self):
        """Test creating client with empty string API key."""
        factory = PlatformFactory()
        config = {"api_key": ""}

        with pytest.raises(ValueError, match="API key not configured for platform: vast"):
            factory.create_client("vast", config)

    def test_factory_singleton_behavior(self):
        """Test that factory creates new instances (not singleton)."""
        factory1 = PlatformFactory()
        factory2 = PlatformFactory()

        # Should be different instances
        assert factory1 is not factory2

        # But should have same platform support
        assert factory1.get_supported_platforms() == factory2.get_supported_platforms()

    @patch("variousplug.factory.VastClient")
    @patch("variousplug.factory.RunPodClient")
    def test_multiple_client_creation(self, mock_runpod_client, mock_vast_client):
        """Test creating multiple clients."""
        mock_vast_instance = Mock()
        mock_runpod_instance = Mock()
        mock_vast_client.return_value = mock_vast_instance
        mock_runpod_client.return_value = mock_runpod_instance

        factory = PlatformFactory()

        # Create vast client
        vast_config = {"api_key": "vast_key"}
        vast_client = factory.create_client("vast", vast_config)

        # Create runpod client
        runpod_config = {"api_key": "runpod_key"}
        runpod_client = factory.create_client("runpod", runpod_config)

        # Verify both were created correctly
        assert vast_client == mock_vast_instance
        assert runpod_client == mock_runpod_instance

        mock_vast_client.assert_called_once_with("vast_key")
        mock_runpod_client.assert_called_once_with("runpod_key")

    def test_internal_creator_methods(self):
        """Test internal creator methods."""
        factory = PlatformFactory()

        # Test _create_vast_client
        with patch("variousplug.factory.VastClient") as mock_vast:
            mock_instance = Mock()
            mock_vast.return_value = mock_instance

            result = factory._create_vast_client("test_key")

            assert result == mock_instance
            mock_vast.assert_called_once_with("test_key")

        # Test _create_runpod_client
        with patch("variousplug.factory.RunPodClient") as mock_runpod:
            mock_instance = Mock()
            mock_runpod.return_value = mock_instance

            result = factory._create_runpod_client("test_key")

            assert result == mock_instance
            mock_runpod.assert_called_once_with("test_key")

    def test_file_sync_creation_consistency(self):
        """Test that file sync creation is consistent."""
        factory = PlatformFactory()

        # Create multiple file sync instances for same platform
        config = {"api_key": "test_key"}
        sync1 = factory.create_file_sync("vast", config)
        sync2 = factory.create_file_sync("vast", config)

        # Should be different instances
        assert sync1 is not sync2

        # But should be same type
        assert type(sync1) is type(sync2)

    def test_platform_case_sensitivity(self):
        """Test platform names are case sensitive."""
        factory = PlatformFactory()
        config = {"api_key": "test_key"}

        # Lowercase should work
        factory.create_client("vast", config)

        # Uppercase should fail
        with pytest.raises(ValueError, match="Unsupported platform: VAST"):
            factory.create_client("VAST", config)
