"""Unit tests for configuration handling"""

import pytest
import os
from pathlib import Path

from app.config import Settings


class TestSettings:
    """Tests for application settings"""

    def test_default_settings(self):
        """Test default settings values"""
        # Clear env vars to test defaults
        for key in ["DATABASE_URL", "HOST", "PORT", "LOG_LEVEL", "NODE_TIMEOUT", "HEARTBEAT_GRACE", "API_PREFIX", "CORS_ORIGINS"]:
            os.environ.pop(key, None)

        settings = Settings()

        assert settings.database_url == "sqlite:///./aetheredge.db"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8080
        assert settings.log_level == "info"
        assert settings.node_timeout == 30
        assert settings.heartbeat_grace == 5
        assert settings.api_prefix == "/api/v1"
        assert settings.cors_origins == ["http://localhost:5173", "http://localhost:3000"]

    def test_settings_from_env(self):
        """Test settings loaded from environment variables"""
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
        os.environ["HOST"] = "127.0.0.1"
        os.environ["PORT"] = "9000"
        os.environ["LOG_LEVEL"] = "debug"
        os.environ["NODE_TIMEOUT"] = "60"
        os.environ["HEARTBEAT_GRACE"] = "10"
        os.environ["API_PREFIX"] = "/api/v2"
        os.environ["CORS_ORIGINS"] = '["http://example.com"]'

        settings = Settings()

        assert settings.database_url == "postgresql://user:pass@localhost/db"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.log_level == "debug"
        assert settings.node_timeout == 60
        assert settings.heartbeat_grace == 10
        assert settings.api_prefix == "/api/v2"
        assert settings.cors_origins == ["http://example.com"]

        # Cleanup
        for key in ["DATABASE_URL", "HOST", "PORT", "LOG_LEVEL", "NODE_TIMEOUT", "HEARTBEAT_GRACE", "API_PREFIX", "CORS_ORIGINS"]:
            os.environ.pop(key, None)

    def test_settings_case_insensitive(self):
        """Test settings are case insensitive"""
        os.environ["database_url"] = "sqlite:///test.db"
        os.environ["host"] = "localhost"

        settings = Settings()

        assert settings.database_url == "sqlite:///test.db"
        assert settings.host == "localhost"

        os.environ.pop("database_url", None)
        os.environ.pop("host", None)

    def test_settings_extra_ignored(self):
        """Test extra environment variables are ignored"""
        os.environ["UNKNOWN_SETTING"] = "value"

        # Should not raise
        settings = Settings()
        assert settings.database_url == "sqlite:///./aetheredge.db"

        os.environ.pop("UNKNOWN_SETTING", None)


class TestEdgeConfig:
    """Tests for edge daemon configuration (if config.py exists in edge)"""

    def test_config_file_parsing(self):
        """Test edge config file parsing"""
        # This would test edge/config.rs Config::load()
        # Skipped as it requires Rust test environment
        pass