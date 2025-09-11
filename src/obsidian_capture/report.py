"""
Summary reporting functions for capture results.

This module handles formatting of capture results and errors
for both JSON and text output formats.
"""

import json
import sys
from typing import Any, Dict

from .capture import CaptureResult, DryRunResult
from .errors import CaptureError


def format_success_json(result: CaptureResult) -> str:
    """Format successful capture result as JSON."""
    success_data = {
        "status": "ok",
        "url": result.url,
        "filename": result.file_path.name,
        "path": str(result.file_path),
        "selector": result.selector_used,
        "extracted_chars": result.extracted_chars,
        "markdown_chars": result.markdown_chars,
        "elapsed_ms": result.elapsed_ms,
        "fields": result.front_matter_fields,
    }

    # Add optional metadata fields if present
    if result.metadata.published_at:
        success_data["published_at"] = result.metadata.published_at
    if result.metadata.author:
        success_data["author"] = result.metadata.author

    return json.dumps(success_data)


def format_success_text(result: CaptureResult) -> str:
    """Format successful capture result as human-readable text."""
    lines = [
        f"✓ Successfully captured: {result.url}",
        f"  Saved to: {result.file_path}",
        f"  Selector: {result.selector_used}",
        f"  Content: {result.extracted_chars} chars → {result.markdown_chars} chars markdown",
        f"  Elapsed: {result.elapsed_ms}ms",
    ]
    return "\n".join(lines)


def format_error_json(error: CaptureError, url: str, elapsed_ms: int) -> str:
    """Format error as JSON with context."""
    error_data = error.to_dict()
    error_data.update({"url": url, "elapsed_ms": elapsed_ms})
    return json.dumps(error_data)


def format_error_text(message: str) -> str:
    """Format error as human-readable text."""
    return f"Error: {message}"


def format_dry_run_text(result: DryRunResult) -> str:
    """Format dry run result as human-readable text."""
    import yaml

    # Format front matter nicely
    front_matter_yaml = yaml.dump(
        result.front_matter_fields,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    ).strip()

    output = []
    output.append("🔍 DRY RUN PREVIEW")
    output.append("=" * 50)
    output.append(f"📄 Proposed filename: {result.proposed_filename}")
    output.append(f"🎯 Selector used: {result.selector_used}")
    output.append(f"📊 Content length: {result.markdown_chars:,} characters")
    output.append(f"⏱️  Processing time: {result.elapsed_ms}ms")
    output.append("")
    output.append("📋 FRONT MATTER PREVIEW:")
    output.append("---")
    output.append(front_matter_yaml)
    output.append("---")
    output.append("")
    output.append("✨ This was a preview only - no files were written.")
    output.append("   Remove --dry to actually capture the article.")

    return "\n".join(output)


def format_dry_run_json(result: DryRunResult) -> str:
    """Format dry run result as JSON."""
    import json

    data = {
        "status": "dry_run_preview",
        "url": result.url,
        "proposed_filename": result.proposed_filename,
        "selector_used": result.selector_used,
        "content_stats": {
            "extracted_chars": result.extracted_chars,
            "markdown_chars": result.markdown_chars,
        },
        "elapsed_ms": result.elapsed_ms,
        "front_matter": result.front_matter_fields,
        "metadata": {
            "title": result.metadata.title,
            "author": result.metadata.author,
            "published_at": result.metadata.published_at,
            "description": result.metadata.description,
            "site_name": result.metadata.site_name,
        },
    }

    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def output_success(result: CaptureResult, format_type: str = "text") -> None:
    """Output successful capture result in specified format."""
    if format_type == "json":
        output = format_success_json(result)
    else:
        output = format_success_text(result)

    print(output)


def output_dry_run(result: DryRunResult, format_type: str = "text") -> None:
    """Output dry run preview result in specified format."""
    if format_type == "json":
        output = format_dry_run_json(result)
    else:
        output = format_dry_run_text(result)

    print(output)


def output_error(
    error: CaptureError, url: str, elapsed_ms: int, format_type: str = "text"
) -> None:
    """Output error in specified format."""
    if format_type == "json":
        output = format_error_json(error, url, elapsed_ms)
        print(output)
    else:
        output = format_error_text(str(error))
        print(output, file=sys.stderr)


def output_legacy_error(message: str, format_type: str = "text", **kwargs: Any) -> None:
    """
    Legacy error output function for backwards compatibility.

    This maintains the existing CLI interface while transitioning
    to structured error handling.
    """
    if format_type == "json":
        error_data = {"status": "error", "message": message, **kwargs}
        print(json.dumps(error_data))
    else:
        print(f"Error: {message}", file=sys.stderr)


def generate_summary_stats(result: CaptureResult) -> Dict[str, Any]:
    """Generate summary statistics for capture operation."""
    return {
        "capture_stats": {
            "url": result.url,
            "elapsed_ms": result.elapsed_ms,
            "content_extraction": {
                "selector_used": result.selector_used,
                "original_chars": result.extracted_chars,
                "markdown_chars": result.markdown_chars,
                "compression_ratio": round(
                    result.markdown_chars / result.extracted_chars, 3
                )
                if result.extracted_chars > 0
                else 0,
            },
            "file_info": {
                "filename": result.file_path.name,
                "relative_path": str(
                    result.file_path.relative_to(result.file_path.parents[2])
                ),  # Relative to vault
                "created_at": result.retrieved_at.isoformat(),
            },
            "metadata_extracted": {
                "title": result.metadata.title is not None,
                "author": result.metadata.author is not None,
                "published_at": result.metadata.published_at is not None,
                "front_matter_fields": len(result.front_matter_fields),
            },
        }
    }
