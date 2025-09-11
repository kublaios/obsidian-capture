"""Filename and directory naming strategy."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from slugify import slugify

from .metadata import generate_fallback_slug


class NamingError(Exception):
    """Filename/directory naming error."""

    pass


def generate_filename(title: Optional[str], url: str, max_length: int = 80) -> str:
    """
    Generate safe filename from title or URL.

    Args:
        title: Article title (may be None)
        url: Source URL for fallback
        max_length: Maximum filename length (excluding .md extension)

    Returns:
        Safe filename with .md extension
    """
    logger = logging.getLogger(__name__)

    if title:
        # Use title as primary source
        base_name = slugify(title, max_length=max_length)
        if base_name:
            logger.debug(
                f"Generated filename from title: '{title}' -> '{base_name}.md'"
            )
            return f"{base_name}.md"

    # Fallback to URL-based slug
    base_name = generate_fallback_slug(url, title)
    logger.debug(f"Generated filename from URL fallback: '{url}' -> '{base_name}.md'")

    # Ensure we have something
    if not base_name:
        base_name = "article"

    # Limit length
    if len(base_name) > max_length:
        base_name = base_name[:max_length].rstrip("-_")

    return f"{base_name}.md"


def create_date_directory(vault_path: Path, date: Optional[datetime] = None) -> Path:
    """
    Create date-based directory (YYYY-MM format).

    Args:
        vault_path: Base vault directory
        date: Date to use (defaults to today)

    Returns:
        Path to date directory
    """
    if date is None:
        date = datetime.now()

    date_dir_name = date.strftime("%Y-%m")
    date_dir = vault_path / date_dir_name

    # Create directory if it doesn't exist
    try:
        date_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise NamingError(f"Failed to create date directory {date_dir}: {e}") from e

    return date_dir


def create_full_directory_path(
    vault_path: Path, subfolder: Optional[str] = None, date: Optional[datetime] = None
) -> Path:
    """
    Create full directory path with date and optional subfolder.

    Args:
        vault_path: Base vault directory
        subfolder: Optional subfolder name
        date: Date for directory structure

    Returns:
        Full directory path
    """
    # Start with date directory
    directory = create_date_directory(vault_path, date)

    # Add subfolder if specified
    if subfolder:
        # Clean subfolder name
        clean_subfolder = clean_directory_name(subfolder)
        directory = directory / clean_subfolder

        # Create subfolder
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise NamingError(f"Failed to create subfolder {directory}: {e}") from e

    return directory


def clean_directory_name(name: str) -> str:
    """
    Clean directory name to be filesystem safe.

    Args:
        name: Raw directory name

    Returns:
        Clean directory name
    """
    # Remove/replace unsafe characters
    name = re.sub(r'[<>:"/\\|?*]', "", name)

    # Remove leading/trailing dots and spaces
    name = name.strip(". ")

    # Limit length
    name = name[:50]

    # Ensure not empty
    if not name:
        name = "misc"

    return name


def resolve_final_path(directory: Path, filename: str, overwrite: bool = False) -> Path:
    """
    Resolve final file path, handling collisions with numeric suffixes.

    Args:
        directory: Target directory
        filename: Desired filename
        overwrite: Whether to overwrite existing files

    Returns:
        Final file path (may have numeric suffix)
    """
    file_path = directory / filename

    # If overwrite is enabled or file doesn't exist, use as-is
    if overwrite or not file_path.exists():
        return file_path

    # Handle collision with numeric suffix
    base_name = file_path.stem  # filename without extension
    extension = file_path.suffix  # .md

    counter = 1
    while True:
        # Try with numeric suffix
        new_filename = f"{base_name}-{counter}{extension}"
        new_path = directory / new_filename

        if not new_path.exists():
            return new_path

        counter += 1

        # Safety check to avoid infinite loop
        if counter > 1000:
            raise NamingError(f"Too many filename collisions for {filename}")


def generate_full_path(
    vault_path: Path,
    title: Optional[str],
    url: str,
    subfolder: Optional[str] = None,
    overwrite: bool = False,
    date: Optional[datetime] = None,
    max_filename_length: int = 80,
) -> Path:
    """
    Generate complete file path with directory structure and collision handling.

    Args:
        vault_path: Base vault directory
        title: Article title (may be None)
        url: Source URL
        subfolder: Optional subfolder
        overwrite: Whether to overwrite existing files
        date: Date for directory structure
        max_filename_length: Maximum filename length

    Returns:
        Complete file path
    """
    # Generate filename
    filename = generate_filename(title, url, max_filename_length)

    # Create directory structure
    directory = create_full_directory_path(vault_path, subfolder, date)

    # Resolve final path with collision handling
    final_path = resolve_final_path(directory, filename, overwrite)

    return final_path


def validate_vault_path(vault_path: Path) -> bool:
    """
    Validate that vault path is usable.

    Args:
        vault_path: Path to validate

    Returns:
        True if valid and usable
    """
    try:
        # Check if exists and is directory
        if not vault_path.exists():
            return False

        if not vault_path.is_dir():
            return False

        # Check if writable by trying to create a test file
        test_file = vault_path / ".obsidian_capture_test"
        try:
            test_file.touch()
            test_file.unlink()  # Clean up
            return True
        except Exception:
            return False

    except Exception:
        return False
