"""File writing with front matter generation."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from bs4 import BeautifulSoup

from .config import Config
from .metadata import ArticleMetadata, generate_obsidian_tags


class WriteError(Exception):
    """File writing error."""

    pass


def generate_front_matter(
    metadata: ArticleMetadata,
    config: Config,
    url: str,
    selector: str,
    retrieved_at: Optional[datetime] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    html_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate front matter dictionary.

    Args:
        metadata: Extracted article metadata
        config: Configuration with potential extra fields
        url: Source URL
        selector: CSS selector used for extraction
        retrieved_at: Retrieval timestamp
        extra_fields: Additional fields to include
        html_content: Original HTML content for tag generation

    Returns:
        Front matter dictionary
    """
    if retrieved_at is None:
        retrieved_at = datetime.now()

    # Start with core fields
    front_matter = {
        "source": url,
        "selector": selector,
        "retrieved_at": retrieved_at.isoformat(),
    }

    # Add metadata fields (only non-None values)
    metadata_dict = metadata.to_dict()
    front_matter.update(metadata_dict)

    # Add config extra fields
    if hasattr(config, "extra_fields") and config.extra_fields:
        for key, value in config.extra_fields.items():
            if value is not None:
                front_matter[key] = value

    # Generate and merge tags
    all_tags = []

    # Start with existing tags from metadata
    existing_tags_raw: Any = front_matter.get("tags", [])
    if isinstance(existing_tags_raw, str):
        existing_tags = [existing_tags_raw]
    elif isinstance(existing_tags_raw, list):
        existing_tags = existing_tags_raw
    else:
        existing_tags = []
    all_tags.extend(existing_tags)

    # Add config tags
    if config.tags:
        for tag in config.tags:
            if tag not in all_tags:
                all_tags.append(tag)

    # Generate Obsidian-style tags from HTML content
    if html_content:
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            obsidian_tags = generate_obsidian_tags(soup, url)
            for tag in obsidian_tags:
                if tag not in all_tags:
                    all_tags.append(tag)
        except Exception:
            # If tag generation fails, continue without Obsidian tags
            pass

    # Set tags if we have any
    if all_tags:
        front_matter["tags"] = all_tags  # type: ignore[assignment]

    # Add config summary if present
    if config.summary:
        front_matter["summary"] = config.summary

    # Add config archived_at if present
    if config.archived_at:
        front_matter["archived_at"] = config.archived_at

    # Add any additional extra fields
    if extra_fields:
        front_matter.update(extra_fields)

    # Remove excluded fields
    if config.exclude_fields:
        for field in config.exclude_fields:
            front_matter.pop(field, None)

    return front_matter


def serialize_front_matter(front_matter: Dict[str, Any]) -> str:
    """
    Serialize front matter to YAML string.

    Args:
        front_matter: Front matter dictionary

    Returns:
        YAML front matter string with delimiters
    """
    try:
        # Filter out None values
        clean_front_matter = {
            k: v for k, v in front_matter.items() if v is not None and v != ""
        }

        yaml_content = yaml.dump(
            clean_front_matter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,
        )

        return f"---\n{yaml_content}---\n\n"

    except Exception as e:
        raise WriteError(f"Failed to serialize front matter: {e}") from e


def write_markdown_file(
    file_path: Path,
    front_matter: Dict[str, Any],
    markdown_content: str,
    create_directories: bool = True,
) -> None:
    """
    Write markdown file with front matter.

    Args:
        file_path: Path to write file
        front_matter: Front matter dictionary
        markdown_content: Markdown content
        create_directories: Whether to create parent directories

    Raises:
        WriteError: If writing fails
    """
    try:
        # Create parent directories if needed
        if create_directories:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate front matter YAML
        front_matter_yaml = serialize_front_matter(front_matter)

        # Combine front matter and content
        full_content = front_matter_yaml + markdown_content

        # Write file
        file_path.write_text(full_content, encoding="utf-8")

    except Exception as e:
        raise WriteError(f"Failed to write file {file_path}: {e}") from e


def get_front_matter_fields(front_matter: Dict[str, Any]) -> List[str]:
    """
    Get list of field names present in front matter.

    Args:
        front_matter: Front matter dictionary

    Returns:
        List of field names
    """
    return [
        key for key, value in front_matter.items() if value is not None and value != ""
    ]


def create_note_file(
    file_path: Path,
    metadata: ArticleMetadata,
    config: Config,
    markdown_content: str,
    url: str,
    selector: str,
    retrieved_at: Optional[datetime] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    html_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create complete note file with front matter and content.

    Args:
        file_path: Where to write the file
        metadata: Extracted metadata
        config: Configuration
        markdown_content: Converted markdown content
        url: Source URL
        selector: Selector used for extraction
        retrieved_at: Retrieval timestamp
        extra_fields: Additional fields
        html_content: Original HTML content for tag generation

    Returns:
        The generated front matter dictionary

    Raises:
        WriteError: If file creation fails
    """
    # Generate front matter
    front_matter = generate_front_matter(
        metadata=metadata,
        config=config,
        url=url,
        selector=selector,
        retrieved_at=retrieved_at,
        extra_fields=extra_fields,
        html_content=html_content,
    )

    # Write file
    write_markdown_file(
        file_path=file_path,
        front_matter=front_matter,
        markdown_content=markdown_content,
    )

    return front_matter
