"""Content extraction using CSS selectors."""

import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup, Tag


class ExtractionError(Exception):
    """Content extraction error."""

    pass


class NoSelectorMatchError(ExtractionError):
    """No selector matched sufficient content."""

    pass


@dataclass
class ExtractionResult:
    """Result of content extraction."""

    html_fragment: str
    text_content: str
    selector: str
    character_count: int
    attempted_selectors: List[str]


def clean_text(text: str) -> str:
    """Clean extracted text content."""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove excessive newlines
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # Trim
    text = text.strip()

    return text


def extract_content_with_selectors(
    html_content: str, selectors: List[str], min_chars: int = 80
) -> ExtractionResult:
    """
    Extract content using ordered list of selectors.

    Args:
        html_content: Raw HTML content
        selectors: Ordered list of CSS selectors to try
        min_chars: Minimum character count required

    Returns:
        ExtractionResult with extracted content

    Raises:
        NoSelectorMatchError: If no selector produces sufficient content
        ExtractionError: If extraction fails
    """
    if not selectors:
        raise ExtractionError("No selectors provided")

    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except Exception as e:
        raise ExtractionError(f"Failed to parse HTML: {e}") from e

    attempted_selectors = []

    for selector in selectors:
        attempted_selectors.append(selector)

        try:
            # Find all matching elements
            elements = soup.select(selector)

            if not elements:
                continue

            # Try each matching element
            for element in elements:
                # Extract HTML fragment
                html_fragment = str(element)

                # Extract text content
                text_content = element.get_text(separator=" ", strip=True)
                text_content = clean_text(text_content)

                # Check if meets minimum length requirement
                if len(text_content) >= min_chars:
                    return ExtractionResult(
                        html_fragment=html_fragment,
                        text_content=text_content,
                        selector=selector,
                        character_count=len(text_content),
                        attempted_selectors=attempted_selectors,
                    )

        except Exception:
            # Log selector error but continue to next selector
            continue

    # No selector produced sufficient content
    raise NoSelectorMatchError(
        f"No selector matched content with at least {min_chars} characters. "
        f"Tried selectors: {attempted_selectors}"
    )


def extract_element_by_selector(soup: BeautifulSoup, selector: str) -> Optional[Tag]:
    """
    Extract first matching element by CSS selector.

    Args:
        soup: BeautifulSoup parsed document
        selector: CSS selector string

    Returns:
        First matching Tag element or None
    """
    try:
        elements = soup.select(selector)
        return elements[0] if elements else None
    except Exception:
        return None


def get_clean_text_content(element: Tag) -> str:
    """
    Get clean text content from element.

    Args:
        element: BeautifulSoup Tag element

    Returns:
        Clean text content
    """
    text = element.get_text(separator=" ", strip=True)
    return clean_text(text)
