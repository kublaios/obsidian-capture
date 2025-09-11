"""Unit tests for config validation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from src.obsidian_capture.config import (
    Config,
    ConfigError,
    create_default_config,
    load_config,
)


class TestConfig:
    """Test Config class validation."""

    def test_config_minimal_valid(self):
        """Test creating config with minimal valid parameters."""
        config = Config(selectors=["article", "main"])

        assert config.selectors == ["article", "main"]
        assert config.min_content_chars == 80
        assert config.overwrite is False
        assert config.subfolder is None
        assert config.tags == []
        assert config.summary is None
        assert config.archived_at is None
        assert config.extra_fields == {}

    def test_config_all_parameters(self):
        """Test creating config with all parameters."""
        config = Config(
            selectors=["article", "main"],
            min_content_chars=100,
            overwrite=True,
            subfolder="articles",
            tags=["web", "content"],
            summary="Test summary",
            archived_at="2023-10-15T10:00:00Z",
            custom_field="custom_value",
        )

        assert config.selectors == ["article", "main"]
        assert config.min_content_chars == 100
        assert config.overwrite is True
        assert config.subfolder == "articles"
        assert config.tags == ["web", "content"]
        assert config.summary == "Test summary"
        assert config.archived_at == "2023-10-15T10:00:00Z"
        assert config.extra_fields == {"custom_field": "custom_value"}

    def test_config_empty_selectors(self):
        """Test config validation fails with empty selectors list."""
        with pytest.raises(
            ConfigError, match="At least one selector must be specified"
        ):
            Config(selectors=[])

    def test_config_no_selectors(self):
        """Test config validation fails with None selectors."""
        with pytest.raises(
            ConfigError, match="At least one selector must be specified"
        ):
            Config(selectors=None)

    def test_config_invalid_min_content_chars(self):
        """Test config validation fails with invalid min_content_chars."""
        with pytest.raises(ConfigError, match="min_content_chars must be at least 1"):
            Config(selectors=["article"], min_content_chars=0)

        with pytest.raises(ConfigError, match="min_content_chars must be at least 1"):
            Config(selectors=["article"], min_content_chars=-1)

    def test_config_invalid_selectors(self):
        """Test config validation fails with invalid selectors."""
        with pytest.raises(ConfigError, match="Invalid selector"):
            Config(selectors=["article", ""])

        with pytest.raises(ConfigError, match="Invalid selector"):
            Config(selectors=["article", None])

        with pytest.raises(ConfigError, match="Invalid selector"):
            Config(selectors=["article", "   "])

    def test_config_invalid_subfolder_type(self):
        """Test config validation fails with invalid subfolder type."""
        with pytest.raises(ConfigError, match="subfolder must be a string"):
            Config(selectors=["article"], subfolder=123)

    def test_config_invalid_subfolder_path(self):
        """Test config validation fails with unsafe subfolder paths."""
        with pytest.raises(ConfigError, match="Invalid subfolder path"):
            Config(selectors=["article"], subfolder="../dangerous")

        with pytest.raises(ConfigError, match="Invalid subfolder path"):
            Config(selectors=["article"], subfolder="folder/./subfolder")

        with pytest.raises(ConfigError, match="Invalid subfolder path"):
            Config(selectors=["article"], subfolder="folder/.hidden")

    def test_config_valid_subfolder_paths(self):
        """Test config accepts valid subfolder paths."""
        # Simple folder name
        config = Config(selectors=["article"], subfolder="articles")
        assert config.subfolder == "articles"

        # Folder with path separator
        config = Config(selectors=["article"], subfolder="web/articles")
        assert config.subfolder == "web/articles"

    def test_config_none_tags_becomes_empty_list(self):
        """Test that None tags becomes empty list."""
        config = Config(selectors=["article"], tags=None)
        assert config.tags == []

    def test_config_preserves_tag_list(self):
        """Test that tag list is preserved."""
        tags = ["tag1", "tag2"]
        config = Config(selectors=["article"], tags=tags)
        assert config.tags == tags
        # Tags are preserved (may or may not be copied based on implementation)

    def test_config_to_dict_minimal(self):
        """Test converting minimal config to dict."""
        config = Config(selectors=["article"])
        result = config.to_dict()

        expected = {
            "selectors": ["article"],
            "min_content_chars": 80,
            "overwrite": False,
        }
        assert result == expected

    def test_config_to_dict_complete(self):
        """Test converting complete config to dict."""
        config = Config(
            selectors=["article", "main"],
            min_content_chars=100,
            overwrite=True,
            subfolder="articles",
            tags=["web", "content"],
            summary="Test summary",
            archived_at="2023-10-15T10:00:00Z",
            custom_field="custom_value",
        )
        result = config.to_dict()

        expected = {
            "selectors": ["article", "main"],
            "min_content_chars": 100,
            "overwrite": True,
            "subfolder": "articles",
            "tags": ["web", "content"],
            "summary": "Test summary",
            "archived_at": "2023-10-15T10:00:00Z",
            "custom_field": "custom_value",
        }
        assert result == expected

    def test_config_from_dict_minimal(self):
        """Test creating config from minimal dict."""
        data = {"selectors": ["article", "main"]}
        config = Config.from_dict(data)

        assert config.selectors == ["article", "main"]
        assert config.min_content_chars == 80
        assert config.overwrite is False

    def test_config_from_dict_complete(self):
        """Test creating config from complete dict."""
        data = {
            "selectors": ["article", "main"],
            "min_content_chars": 100,
            "overwrite": True,
            "subfolder": "articles",
            "tags": ["web", "content"],
            "summary": "Test summary",
            "archived_at": "2023-10-15T10:00:00Z",
            "custom_field": "custom_value",
        }
        config = Config.from_dict(data)

        assert config.selectors == ["article", "main"]
        assert config.min_content_chars == 100
        assert config.overwrite is True
        assert config.subfolder == "articles"
        assert config.tags == ["web", "content"]
        assert config.summary == "Test summary"
        assert config.archived_at == "2023-10-15T10:00:00Z"
        assert config.extra_fields == {"custom_field": "custom_value"}

    def test_config_from_dict_missing_selectors(self):
        """Test config from dict fails without selectors."""
        data = {"min_content_chars": 100}
        with pytest.raises(
            ConfigError, match="Configuration must include 'selectors' field"
        ):
            Config.from_dict(data)

    def test_config_from_dict_empty_selectors(self):
        """Test config from dict fails with empty selectors."""
        data = {"selectors": []}
        with pytest.raises(
            ConfigError, match="Configuration must include 'selectors' field"
        ):
            Config.from_dict(data)

    def test_config_from_dict_with_defaults(self):
        """Test config from dict uses defaults for optional fields."""
        data = {"selectors": ["article"]}
        config = Config.from_dict(data)

        assert config.min_content_chars == 80  # Default
        assert config.overwrite is False  # Default
        assert config.subfolder is None  # Default
        assert config.tags == []  # Default

    def test_config_roundtrip(self):
        """Test config can be converted to dict and back."""
        original = Config(
            selectors=["article", "main"],
            min_content_chars=100,
            overwrite=True,
            subfolder="articles",
            tags=["web"],
            summary="Test",
            custom_field="value",
        )

        data = original.to_dict()
        restored = Config.from_dict(data)

        assert restored.selectors == original.selectors
        assert restored.min_content_chars == original.min_content_chars
        assert restored.overwrite == original.overwrite
        assert restored.subfolder == original.subfolder
        assert restored.tags == original.tags
        assert restored.summary == original.summary
        assert restored.extra_fields == original.extra_fields


class TestLoadConfig:
    """Test configuration loading from files."""

    def test_load_config_yaml(self):
        """Test loading YAML config file."""
        config_data = {
            "selectors": ["article", "main"],
            "min_content_chars": 100,
            "overwrite": True,
            "tags": ["web", "content"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)

            assert config.selectors == ["article", "main"]
            assert config.min_content_chars == 100
            assert config.overwrite is True
            assert config.tags == ["web", "content"]
        finally:
            config_path.unlink()

    def test_load_config_yml_extension(self):
        """Test loading config with .yml extension."""
        config_data = {"selectors": ["article"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.selectors == ["article"]
        finally:
            config_path.unlink()

    def test_load_config_unknown_extension(self):
        """Test loading config with unknown extension tries YAML."""
        config_data = {"selectors": ["article"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.selectors == ["article"]
        finally:
            config_path.unlink()

    def test_load_config_nonexistent_file(self):
        """Test loading nonexistent config file."""
        config_path = Path("/nonexistent/config.yaml")

        with pytest.raises(ConfigError, match="Config file does not exist"):
            load_config(config_path)

    def test_load_config_read_error(self):
        """Test loading config when file can't be read."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            config_path = Path(f.name)

        try:
            # Make file unreadable by mocking read_text to fail
            with patch.object(
                Path, "read_text", side_effect=PermissionError("Access denied")
            ):
                with pytest.raises(ConfigError, match="Failed to read config file"):
                    load_config(config_path)
        finally:
            config_path.unlink()

    def test_load_config_invalid_yaml(self):
        """Test loading config with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(ConfigError, match="Failed to parse YAML config"):
                load_config(config_path)
        finally:
            config_path.unlink()

    def test_load_config_not_dict(self):
        """Test loading config that doesn't contain a dict at root."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- item1\n- item2")  # List instead of dict
            config_path = Path(f.name)

        try:
            with pytest.raises(
                ConfigError,
                match="Config file must contain a mapping/object at root level",
            ):
                load_config(config_path)
        finally:
            config_path.unlink()

    def test_load_config_invalid_config_data(self):
        """Test loading config with valid YAML but invalid config data."""
        config_data = {"invalid_field": "no selectors"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            with pytest.raises(
                ConfigError, match="Configuration must include 'selectors' field"
            ):
                load_config(config_path)
        finally:
            config_path.unlink()

    def test_load_config_encoding_utf8(self):
        """Test loading config with UTF-8 encoding."""
        config_data = {
            "selectors": ["article"],
            "summary": "Test with émojis and ünïcödé",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config_data, f, allow_unicode=True)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.summary == "Test with émojis and ünïcödé"
        finally:
            config_path.unlink()


class TestCreateDefaultConfig:
    """Test default configuration creation."""

    def test_create_default_config(self):
        """Test creating default configuration."""
        config = create_default_config()

        assert isinstance(config, Config)
        assert len(config.selectors) > 0
        assert "article" in config.selectors
        assert "main" in config.selectors
        assert "body" in config.selectors
        assert config.min_content_chars == 80
        assert config.overwrite is False
        assert config.subfolder is None

    def test_default_config_has_common_selectors(self):
        """Test default config includes common content selectors."""
        config = create_default_config()

        expected_selectors = [
            "article",
            "main",
            '[role="main"]',
            ".content",
            ".post-content",
            ".entry-content",
            ".article-content",
            "body",
        ]

        for selector in expected_selectors:
            assert selector in config.selectors

    def test_default_config_is_valid(self):
        """Test default config passes validation."""
        config = create_default_config()

        # Should not raise any exceptions
        assert config.selectors
        assert config.min_content_chars >= 1

        # Should be able to convert to dict and back
        data = config.to_dict()
        restored = Config.from_dict(data)
        assert restored.selectors == config.selectors
