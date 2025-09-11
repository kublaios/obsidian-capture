"""HTML element exclusion by CSS selectors."""

import re
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from .logging import get_logger

# Primary content element selectors
PRIMARY_CONTENT_SELECTORS = ["article", "main", '[role="main"]']


@dataclass
class ExclusionSelector:
    """Represents a CSS selector used for exclusion."""

    selector: str
    reason: Optional[str] = None


@dataclass
class SelectorResult:
    """Result of applying a single CSS selector."""

    selector: str
    success: bool
    elements_removed: int
    error_message: Optional[str] = None


@dataclass
class ExclusionSummary:
    """Summary of exclusion operation results."""

    selectors_processed: int
    elements_removed: int
    original_element_count: int
    successful_selectors: int
    failed_selectors: int
    empty_primary_content_warning: bool = False

    @property
    def removal_ratio(self) -> float:
        """Calculate the ratio of elements removed to original count."""
        if self.original_element_count == 0:
            return 0.0
        return self.elements_removed / self.original_element_count

    @property
    def high_removal_warning(self) -> bool:
        """Flag if removal ratio exceeds warning threshold (40%)."""
        return self.removal_ratio >= 0.4


@dataclass
class ValidationResult:
    """Result of selector validation."""

    valid: List[ExclusionSelector]
    invalid: List[ExclusionSelector]
    total_count: int = 0
    cap_exceeded: bool = False


class TooManySelectorError(Exception):
    """Raised when selector count exceeds the maximum limit."""

    pass


def is_protected_selector(selector: str) -> bool:
    """Check if a CSS selector targets protected root elements (html, body)."""
    if not selector or not isinstance(selector, str):
        return False

    selector_lower = selector.lower().strip()

    # Check for exact matches or selectors starting with html/body
    protected_patterns = [
        r"^html\b",  # html, html.class, html *
        r"^body\b",  # body, body.class, body *
    ]

    for pattern in protected_patterns:
        if re.match(pattern, selector_lower):
            return True

    return False


def validate_selectors(
    selectors: List[str], max_selectors: int = 100
) -> ValidationResult:
    """
    Validate a list of CSS selectors.

    Args:
        selectors: List of CSS selector strings to validate
        max_selectors: Maximum number of selectors allowed (default: 100)

    Returns:
        ValidationResult with valid/invalid selector lists

    Raises:
        TooManySelectorError: If selector count exceeds maximum
    """
    total_count = len(selectors)

    if total_count > max_selectors:
        raise TooManySelectorError(
            f"Too many selectors: {total_count} provided, limit is {max_selectors}"
        )

    valid = []
    invalid = []

    for selector in selectors:
        if not selector or not isinstance(selector, str):
            invalid.append(
                ExclusionSelector(
                    selector=selector or "", reason="Empty or invalid selector"
                )
            )
            continue

        # Check if selector is protected
        if is_protected_selector(selector):
            invalid.append(
                ExclusionSelector(
                    selector=selector,
                    reason="Protected selector (html/body cannot be excluded)",
                )
            )
            continue

        # Validate CSS selector syntax
        try:
            # Use BeautifulSoup's CSS parser to validate syntax
            soup = BeautifulSoup("<div></div>", "html.parser")
            soup.select(selector)  # This will raise an exception if invalid
            valid.append(ExclusionSelector(selector=selector))
        except Exception as e:
            invalid.append(
                ExclusionSelector(
                    selector=selector, reason=f"Invalid CSS selector syntax: {str(e)}"
                )
            )

    return ValidationResult(
        valid=valid, invalid=invalid, total_count=total_count, cap_exceeded=False
    )


@dataclass
class ExclusionResult:
    """Result of applying exclusion selectors to HTML."""

    soup: BeautifulSoup
    summary: ExclusionSummary
    selector_results: List[SelectorResult]


def apply_exclusions(soup: BeautifulSoup, selectors: List[str]) -> ExclusionResult:
    """
    Apply CSS selectors to exclude elements from HTML document.

    Args:
        soup: BeautifulSoup object to modify
        selectors: List of CSS selector strings

    Returns:
        ExclusionResult containing modified soup and summary
    """
    # Count original elements before any modifications
    original_element_count = len(soup.find_all())

    # Validate selectors first
    try:
        validation = validate_selectors(selectors)
    except TooManySelectorError:
        # Re-raise the error, caller should handle it
        raise

    selector_results = []
    total_removed = 0

    # Process valid selectors
    for exclusion_selector in validation.valid:
        selector = exclusion_selector.selector
        try:
            # Find elements matching the selector
            matching_elements = soup.select(selector)
            elements_removed = len(matching_elements)

            # Remove the matched elements
            for element in matching_elements:
                element.decompose()  # Remove element and free memory

            total_removed += elements_removed

            selector_results.append(
                SelectorResult(
                    selector=selector,
                    success=True,
                    elements_removed=elements_removed,
                    error_message=None,
                )
            )

        except Exception as e:
            # CSS selector execution failed
            selector_results.append(
                SelectorResult(
                    selector=selector,
                    success=False,
                    elements_removed=0,
                    error_message=f"Failed to apply selector: {str(e)}",
                )
            )

    # Process invalid selectors (they are already validated as invalid)
    for exclusion_selector in validation.invalid:
        selector_results.append(
            SelectorResult(
                selector=exclusion_selector.selector,
                success=False,
                elements_removed=0,
                error_message=exclusion_selector.reason,
            )
        )

    # Generate summary
    summary = aggregate_exclusion_summary(
        selector_results, original_element_count, soup
    )

    return ExclusionResult(
        soup=soup, summary=summary, selector_results=selector_results
    )


def is_content_element_empty(element: Tag) -> bool:
    """
    Check if a content element is effectively empty.

    Args:
        element: BeautifulSoup element to check

    Returns:
        True if element is empty, False if it has meaningful content
    """
    return not has_meaningful_content(element)


def detect_empty_primary_content(soup: BeautifulSoup) -> bool:
    """
    Detect if primary content elements are empty after exclusions.

    Args:
        soup: BeautifulSoup object after exclusions have been applied

    Returns:
        True if primary content is empty or missing, False otherwise
    """
    found_primary_elements: List[Tag] = []

    # Find all primary content elements
    for selector in PRIMARY_CONTENT_SELECTORS:
        elements = soup.select(selector)
        found_primary_elements.extend(elements)

    # If no primary elements exist, it's a warning condition
    if not found_primary_elements:
        return True

    # Check if at least one primary element has meaningful content
    for element in found_primary_elements:
        if has_meaningful_content(element):
            return False

    # All primary elements are empty
    return True


def has_meaningful_content(element: Tag) -> bool:
    """
    Check if an element has meaningful content (text, images, links, etc.).

    Args:
        element: BeautifulSoup element to check

    Returns:
        True if element has meaningful content, False otherwise
    """
    # Check for images
    if element.find_all("img"):
        return True

    # Check for links
    if element.find_all("a"):
        return True

    # Check for meaningful text content (more than just whitespace)
    text = element.get_text(strip=True)
    if text and len(text) > 0:
        return True

    # Check for other content elements (videos, forms, etc.)
    content_tags = element.find_all(
        ["video", "audio", "iframe", "form", "table", "canvas", "svg"]
    )
    if content_tags:
        return True

    return False


def calculate_removal_ratio(removed_elements: int, original_elements: int) -> float:
    """
    Calculate the ratio of removed elements to original elements.

    Args:
        removed_elements: Number of elements removed
        original_elements: Original number of elements

    Returns:
        Ratio as a float (0.0 to 1.0)
    """
    if original_elements == 0:
        return 0.0
    return removed_elements / original_elements


def should_warn_high_removal(removal_ratio: float) -> bool:
    """
    Determine if removal ratio exceeds warning threshold.

    Args:
        removal_ratio: Ratio of removed to original elements (0.0 to 1.0)

    Returns:
        True if ratio exceeds warning threshold (40%), False otherwise
    """
    return removal_ratio >= 0.4


def aggregate_exclusion_summary(
    selector_results: List[SelectorResult], original_count: int, soup: BeautifulSoup
) -> ExclusionSummary:
    """
    Aggregate selector results into an exclusion summary.

    Args:
        selector_results: List of SelectorResult objects
        original_count: Original element count before exclusions
        soup: BeautifulSoup object after exclusions (for empty content detection)

    Returns:
        ExclusionSummary with aggregated statistics
    """
    selectors_processed = len(selector_results)
    successful_selectors = sum(1 for r in selector_results if r.success)
    failed_selectors = sum(1 for r in selector_results if not r.success)
    elements_removed = sum(r.elements_removed for r in selector_results)

    # Detect empty primary content
    empty_primary_warning = detect_empty_primary_content(soup)

    return ExclusionSummary(
        selectors_processed=selectors_processed,
        elements_removed=elements_removed,
        original_element_count=original_count,
        successful_selectors=successful_selectors,
        failed_selectors=failed_selectors,
        empty_primary_content_warning=empty_primary_warning,
    )


def log_exclusion_warnings(
    exclusion_result: ExclusionResult, logger_name: Optional[str] = None
) -> None:
    """
    Log warnings and summary for exclusion operations.

    Args:
        exclusion_result: Result of exclusion operations
        logger_name: Optional logger name to use
    """
    logger = get_logger(logger_name)
    summary = exclusion_result.summary

    # Log invalid selectors
    invalid_selectors = [r for r in exclusion_result.selector_results if not r.success]
    if invalid_selectors:
        for result in invalid_selectors:
            logger.warning(
                "Exclusion selector failed",
                extra={
                    "selector": result.selector,
                    "error": result.error_message,
                    "operation": "exclude",
                },
            )

    # Log high removal warning
    if summary.high_removal_warning:
        logger.warning(
            f"High removal ratio detected: {summary.removal_ratio:.1%} of elements removed "
            f"({summary.elements_removed}/{summary.original_element_count})",
            extra={
                "removal_ratio": summary.removal_ratio,
                "elements_removed": summary.elements_removed,
                "original_count": summary.original_element_count,
                "warning_type": "high_removal",
            },
        )

    # Log empty primary content warning
    if summary.empty_primary_content_warning:
        logger.warning(
            "Primary content elements (article, main) appear to be empty after exclusions",
            extra={
                "warning_type": "empty_primary_content",
                "elements_removed": summary.elements_removed,
                "operation": "exclude",
            },
        )

    # Log summary info
    if summary.elements_removed > 0:
        logger.info(
            f"Exclusion summary: {summary.successful_selectors}/{summary.selectors_processed} "
            f"selectors successful, {summary.elements_removed} elements removed "
            f"({summary.removal_ratio:.1%} of document)",
            extra={
                "selectors_processed": summary.selectors_processed,
                "successful_selectors": summary.successful_selectors,
                "failed_selectors": summary.failed_selectors,
                "elements_removed": summary.elements_removed,
                "removal_ratio": summary.removal_ratio,
                "operation": "exclude",
            },
        )


def log_exclusion_errors(
    error: Exception, selectors: List[str], logger_name: Optional[str] = None
) -> None:
    """
    Log exclusion operation errors.

    Args:
        error: Exception that occurred
        selectors: List of selectors that caused the error
        logger_name: Optional logger name to use
    """
    logger = get_logger(logger_name)

    if isinstance(error, TooManySelectorError):
        logger.warning(
            f"Too many exclusion selectors provided: {len(selectors)} selectors exceed limit",
            extra={
                "selector_count": len(selectors),
                "error_type": "too_many_selectors",
                "operation": "exclude",
            },
        )
    else:
        logger.error(
            f"Exclusion operation failed: {str(error)}",
            extra={
                "error": str(error),
                "selector_count": len(selectors),
                "error_type": type(error).__name__,
                "operation": "exclude",
            },
        )
