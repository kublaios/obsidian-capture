"""Configuration loader and validation."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigError(Exception):
    """Configuration-related error."""

    pass


class Config:
    """Configuration container with validation."""

    def __init__(
        self,
        selectors: List[str],
        min_content_chars: int = 80,
        overwrite: bool = False,
        subfolder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        archived_at: Optional[str] = None,
        exclusion_selectors: Optional[List[str]] = None,
        vault: Optional[str] = None,
        exclude_fields: Optional[List[str]] = None,
        **extra_fields: Any,
    ) -> None:
        """
        Initialize configuration.

        Args:
            selectors: Ordered list of CSS selectors to try
            min_content_chars: Minimum characters required for content
            overwrite: Whether to overwrite existing files
            subfolder: Subfolder within vault for organization
            tags: List of tags to add to front matter
            summary: Optional summary text
            archived_at: Optional archive timestamp
            exclusion_selectors: Optional list of CSS selectors to exclude
            vault: Optional path to vault directory
            exclude_fields: Optional list of fields to exclude from front matter
            **extra_fields: Additional metadata fields
        """
        if not selectors:
            raise ConfigError("At least one selector must be specified")

        if min_content_chars < 1:
            raise ConfigError("min_content_chars must be at least 1")

        # Validate selectors are valid CSS selector strings
        for selector in selectors:
            if not isinstance(selector, str) or not selector.strip():
                raise ConfigError(f"Invalid selector: {selector}")

        # Validate subfolder path if provided
        if subfolder:
            if not isinstance(subfolder, str):
                raise ConfigError("subfolder must be a string")
            # Check for unsafe path characters
            if (
                ".." in subfolder
                or "/" in subfolder.replace("\\", "/")
                and not all(
                    part.strip() and not part.startswith(".")
                    for part in subfolder.split("/")
                )
            ):
                raise ConfigError(f"Invalid subfolder path: {subfolder}")

        self.selectors = selectors
        self.min_content_chars = min_content_chars
        self.overwrite = overwrite
        self.subfolder = subfolder
        self.tags = tags or []
        self.summary = summary
        self.archived_at = archived_at
        self.exclusion_selectors = exclusion_selectors or []
        self.vault = vault
        self.exclude_fields = exclude_fields or []
        self.extra_fields = extra_fields

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        # Required field
        selectors = data.get("selectors")
        if not selectors:
            raise ConfigError("Configuration must include 'selectors' field")

        return cls(
            selectors=selectors,
            min_content_chars=data.get("min_content_chars", 80),
            overwrite=data.get("overwrite", False),
            subfolder=data.get("subfolder"),
            tags=data.get("tags"),
            summary=data.get("summary"),
            archived_at=data.get("archived_at"),
            exclusion_selectors=data.get("exclusion_selectors"),
            vault=data.get("vault"),
            exclude_fields=data.get("exclude_fields"),
            **{
                k: v
                for k, v in data.items()
                if k
                not in {
                    "selectors",
                    "min_content_chars",
                    "overwrite",
                    "subfolder",
                    "tags",
                    "summary",
                    "archived_at",
                    "exclusion_selectors",
                    "vault",
                    "exclude_fields",
                }
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        result = {
            "selectors": self.selectors,
            "min_content_chars": self.min_content_chars,
            "overwrite": self.overwrite,
        }

        if self.subfolder:
            result["subfolder"] = self.subfolder
        if self.tags:
            result["tags"] = self.tags
        if self.summary:
            result["summary"] = self.summary
        if self.archived_at:
            result["archived_at"] = self.archived_at
        if self.exclusion_selectors:
            result["exclusion_selectors"] = self.exclusion_selectors
        if self.vault:
            result["vault"] = self.vault
        if self.exclude_fields:
            result["exclude_fields"] = self.exclude_fields

        # Add extra fields
        result.update(self.extra_fields)

        return result


def load_config(config_path: Path) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Loaded and validated configuration

    Raises:
        ConfigError: If file cannot be loaded or is invalid
    """
    if not config_path.exists():
        raise ConfigError(f"Config file does not exist: {config_path}")

    try:
        content = config_path.read_text(encoding="utf-8")
    except Exception as e:
        raise ConfigError(f"Failed to read config file: {e}") from e

    # Parse YAML content
    try:
        data = yaml.safe_load(content)

    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML config: {e}") from e
    except Exception as e:
        raise ConfigError(f"Failed to parse config file: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a mapping/object at root level")

    try:
        return Config.from_dict(data)
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Invalid configuration: {e}") from e


def create_default_config() -> Config:
    """Create a default configuration for testing/fallback."""
    return Config(
        selectors=[
            "article",
            "main",
            '[role="main"]',
            ".content",
            ".post-content",
            ".entry-content",
            ".article-content",
            "body",
        ],
        min_content_chars=80,
    )
