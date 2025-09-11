"""HTML to Markdown conversion."""

import re
from typing import Optional

import html2text


class ConversionError(Exception):
    """HTML to Markdown conversion error."""

    pass


def convert_html_to_markdown(
    html_fragment: str,
    base_url: Optional[str] = None,
    body_width: int = 0,
    preserve_links: bool = True,
) -> str:
    """
    Convert HTML fragment to Markdown.

    Args:
        html_fragment: HTML content to convert
        base_url: Base URL for resolving relative links
        body_width: Line wrap width (0 for no wrapping)
        preserve_links: Whether to preserve link formatting

    Returns:
        Markdown content string

    Raises:
        ConversionError: If conversion fails
    """
    try:
        # Configure html2text converter
        converter = html2text.HTML2Text()

        # Basic configuration
        converter.body_width = body_width
        converter.unicode_snob = True
        converter.escape_snob = True

        # Link handling
        if preserve_links:
            converter.inline_links = True
            converter.protect_links = True
        else:
            converter.ignore_links = True

        # Image handling
        converter.ignore_images = False
        converter.images_to_alt = False

        # List handling
        converter.ul_item_mark = "-"
        converter.emphasis_mark = "*"

        # Skip certain elements that don't add value
        converter.ignore_emphasis = False
        converter.ignore_tables = False

        # Set base URL for relative links if provided
        if base_url:
            converter.baseurl = base_url

        # Convert HTML to Markdown
        markdown = converter.handle(html_fragment)

        # Post-process the markdown
        markdown = post_process_markdown(markdown)

        return markdown

    except Exception as e:
        raise ConversionError(f"Failed to convert HTML to Markdown: {e}") from e


def post_process_markdown(markdown: str) -> str:
    """
    Post-process converted markdown for better formatting.

    Args:
        markdown: Raw markdown from html2text

    Returns:
        Cleaned up markdown
    """
    # Remove excessive blank lines (more than 2 consecutive)
    markdown = re.sub(r"\n\s*\n\s*\n+", "\n\n", markdown)

    # Clean up list formatting - ensure proper spacing
    markdown = re.sub(r"\n([-*+])", r"\n\1", markdown)

    # Clean up numbered list formatting
    markdown = re.sub(r"\n(\d+\.)", r"\n\1", markdown)

    # Fix spacing around headers
    markdown = re.sub(r"\n(#{1,6})\s*([^\n]+)\n", r"\n\1 \2\n\n", markdown)

    # Clean up code block formatting
    markdown = re.sub(r"\n```([^\n]*)\n", r"\n\n```\1\n", markdown)
    markdown = re.sub(r"\n```\n", r"\n```\n\n", markdown)

    # Remove trailing whitespace from lines
    lines = markdown.split("\n")
    lines = [line.rstrip() for line in lines]
    markdown = "\n".join(lines)

    # Ensure content ends with single newline
    markdown = markdown.strip() + "\n"

    return markdown


def clean_markdown_content(markdown: str) -> str:
    """
    Additional cleaning for markdown content.

    Args:
        markdown: Markdown content to clean

    Returns:
        Cleaned markdown content
    """
    # Remove or fix common conversion artifacts

    # Remove empty links
    markdown = re.sub(r"\[\]\([^)]*\)", "", markdown)

    # Fix broken emphasis marks
    markdown = re.sub(r"\*\s+\*", "", markdown)
    markdown = re.sub(r"_\s+_", "", markdown)

    # Clean up table formatting if present
    markdown = re.sub(r"\|\s*\|", "|", markdown)

    # Remove excessive punctuation at line ends
    markdown = re.sub(r"([.!?])\1{2,}", r"\1", markdown)

    return markdown


def estimate_reading_time(markdown: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time for markdown content.

    Args:
        markdown: Markdown content
        words_per_minute: Average reading speed

    Returns:
        Estimated reading time in minutes
    """
    # Remove markdown formatting for word count
    text_only = re.sub(r"[#*_`\[\]()]", "", markdown)
    text_only = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text_only)  # Remove images
    text_only = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text_only)  # Remove links

    # Count words
    words = len(text_only.split())

    # Calculate reading time
    minutes = max(1, round(words / words_per_minute))

    return minutes
