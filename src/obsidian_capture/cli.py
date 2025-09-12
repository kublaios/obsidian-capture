"""CLI entry point for Obsidian Capture."""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Sequence
from urllib.parse import urlparse

from obsidian_capture import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="obsidian-capture",
        description="HTML to Markdown capture tool for Obsidian vault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  obsidian-capture https://example.com/article --vault ~/vault
  obsidian-capture /path/to/article.html --vault ~/vault
  obsidian-capture https://blog.com/post --config config.yaml
  obsidian-capture ~/Downloads/saved-page.html --subfolder articles --format json
  obsidian-capture https://blog.com/post --tags "tutorial,python,web-dev"
  obsidian-capture https://example.com/article --dry  # Preview without writing

Vault path lookup:
  1. Uses --vault path if specified
  2. Uses vault path from config file if specified
  3. Falls back to current directory

Config file lookup:
  1. Uses --config path if specified
  2. Uses ~/.obsidian-capture.yml if it exists
  3. Falls back to built-in defaults
""",
    )

    # Positional arguments
    parser.add_argument(
        "url_or_path",
        help="HTTP/HTTPS URL or local HTML file path to capture (required)",
    )

    # Vault argument (optional if specified in config)
    parser.add_argument(
        "--vault",
        "-v",
        type=Path,
        help="Path to Obsidian vault root (can be specified in config file, defaults to current directory)",
    )

    # Optional arguments
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to config file containing selectors & optional fields (defaults to ~/.obsidian-capture.yml if exists)",
    )

    parser.add_argument(
        "--subfolder",
        "-s",
        help="Additional relative folder beneath date bucket (auto-created)",
    )

    parser.add_argument(
        "--overwrite",
        "-o",
        action="store_true",
        help="Overwrite existing file instead of suffixing",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Network timeout in seconds (default: 30)",
    )

    parser.add_argument(
        "--max-size",
        type=int,
        default=2000000,
        help="Maximum raw HTML bytes (default: 2000000)",
    )

    parser.add_argument(
        "--exclude-selectors",
        "-e",
        action="append",
        help="CSS selector to exclude from HTML (can be repeated, max 100 total)",
    )

    parser.add_argument(
        "--tags",
        "-t",
        help="Additional tags to add to the article (comma-separated). Tags will be formatted as #tag for Obsidian",
    )

    parser.add_argument(
        "--dry",
        action="store_true",
        help="Preview capture without writing files - shows front matter and content length",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output/log format: text (default) or json",
    )

    parser.add_argument(
        "--version", action="version", version=f"Obsidian Capture v{__version__}"
    )

    return parser


def validate_url_or_path(url_or_path: str) -> bool:
    """Validate that input is either a properly formatted URL or an existing file path."""
    # Check if it's a URL
    try:
        parsed = urlparse(url_or_path)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return True
    except Exception:
        pass

    # Check if it's a local file path
    try:
        path = Path(url_or_path)
        # Expand user home directory if needed
        if str(path).startswith("~"):
            path = path.expanduser()
        return path.exists() and path.is_file()
    except Exception:
        pass

    return False


def validate_args(args: argparse.Namespace) -> tuple[bool, Optional[str]]:
    """
    Validate parsed arguments.

    Returns:
        (is_valid, error_message)
    """
    # Validate URL or file path format
    if not validate_url_or_path(args.url_or_path):
        return False, f"Invalid URL format or file does not exist: {args.url_or_path}"

    # Validate vault directory exists if provided
    if args.vault:
        if not args.vault.exists():
            return False, f"Vault directory does not exist: {args.vault}"

        if not args.vault.is_dir():
            return False, f"Vault path is not a directory: {args.vault}"

    # Validate config file exists if provided
    if args.config and not args.config.exists():
        return False, f"Config file does not exist: {args.config}"

    # Validate timeout is positive
    if args.timeout <= 0:
        return False, f"Timeout must be positive: {args.timeout}"

    # Validate max-size is positive
    if args.max_size <= 0:
        return False, f"Max size must be positive: {args.max_size}"

    return True, None


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if argv is None:
        argv = sys.argv[1:]

    start_time = time.time()

    # Import report functions first (needed in except blocks)
    try:
        from .report import output_legacy_error
    except ImportError:
        # Fallback error handling if even the report module fails
        print("Critical import error: Cannot import report module", file=sys.stderr)
        return 1

    # Parse arguments
    parser = create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse calls sys.exit() on --help, --version, or parse errors
        return e.code if e.code is not None and isinstance(e.code, int) else 1

    # Validate arguments
    is_valid, error_msg = validate_args(args)
    if not is_valid:
        elapsed_ms = int((time.time() - start_time) * 1000)
        output_legacy_error(
            error_msg or "Unknown validation error",
            args.format,
            code="CONFIG_ERROR",
            url=args.url_or_path,
            elapsed_ms=elapsed_ms,
        )
        return 9  # CONFIG_ERROR

    # Import core modules
    try:
        from .capture import CaptureRequest, DryRunResult, capture_html_to_obsidian
        from .config import create_default_config, load_config
        from .errors import CaptureError
        from .errors import WriteError as CaptureWriteError
        from .naming import validate_vault_path
        from .report import output_dry_run, output_error, output_success
    except ImportError as e:
        output_legacy_error(
            f"Failed to import required modules: {e}",
            args.format,
            code="IMPORT_ERROR",
            url=args.url_or_path,
            elapsed_ms=int((time.time() - start_time) * 1000),
        )
        return 1

    try:
        # Load configuration
        if args.config:
            config = load_config(args.config)
        else:
            # Check for default config file in home directory
            default_config_path = Path.home() / ".obsidian-capture.yml"
            if default_config_path.exists():
                config = load_config(default_config_path)
            else:
                config = create_default_config()

        # Override config with CLI arguments
        if args.overwrite:
            config.overwrite = True
        if args.subfolder:
            config.subfolder = args.subfolder
        if args.exclude_selectors:
            config.exclusion_selectors = args.exclude_selectors

        # Handle CLI tags - merge with existing config tags
        if args.tags:
            # Parse comma-separated tags
            cli_tags = []
            for tag in args.tags.split(","):
                # Clean the tag and ensure it starts with #
                clean_tag = tag.strip()
                if clean_tag:
                    # Add # prefix if not already present
                    if not clean_tag.startswith("#"):
                        clean_tag = f"#{clean_tag}"
                    cli_tags.append(clean_tag)

            # Merge CLI tags with existing config tags
            existing_tags = config.tags or []
            for tag in cli_tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)

            config.tags = existing_tags

        # Determine vault path: CLI > config > current directory
        if args.vault:
            vault_path = args.vault
        elif config.vault:
            # Expand shell patterns like ~ and relative paths
            expanded_path = Path(config.vault).expanduser().resolve()
            vault_path = expanded_path
        else:
            vault_path = Path.cwd()

        # Validate vault path exists and is a directory
        if not vault_path.exists():
            elapsed_ms = int((time.time() - start_time) * 1000)
            error: CaptureError = CaptureWriteError(
                f"Vault directory does not exist: {vault_path}",
                file_path=str(vault_path),
            )
            output_error(error, args.url_or_path, elapsed_ms, args.format)
            return error.exit_code

        if not vault_path.is_dir():
            elapsed_ms = int((time.time() - start_time) * 1000)
            error = CaptureWriteError(
                f"Vault path is not a directory: {vault_path}",
                file_path=str(vault_path),
            )
            output_error(error, args.url_or_path, elapsed_ms, args.format)
            return error.exit_code

        # Validate vault path is writable
        if not validate_vault_path(vault_path):
            elapsed_ms = int((time.time() - start_time) * 1000)
            error = CaptureWriteError(
                f"Vault path is not writable: {vault_path}", file_path=str(vault_path)
            )
            output_error(error, args.url_or_path, elapsed_ms, args.format)
            return error.exit_code

        # Create capture request
        request = CaptureRequest(
            url_or_path=args.url_or_path,
            vault_path=vault_path,
            config=config,
            timeout=args.timeout,
            max_size=args.max_size,
            dry_run=args.dry,
        )

        # Execute capture through orchestrator
        result = capture_html_to_obsidian(request, start_time)

        # Output success (different handling for dry run)
        if isinstance(result, DryRunResult):
            output_dry_run(result, args.format)
        else:
            output_success(result, args.format)
        return 0

    except CaptureError as e:
        # Handle structured capture errors
        elapsed_ms = int((time.time() - start_time) * 1000)
        output_error(e, args.url, elapsed_ms, args.format)
        return e.exit_code

    except Exception as e:
        # Catch-all for unexpected errors
        elapsed_ms = int((time.time() - start_time) * 1000)
        from .errors import GenericError

        error = GenericError(f"Unexpected error: {e}")
        output_error(error, args.url_or_path, elapsed_ms, args.format)
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
