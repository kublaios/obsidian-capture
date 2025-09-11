"""
Orchestrator module for HTML capture process.

This module provides the main orchestration function that coordinates
the entire capture workflow: fetch → extract → metadata → convert → write.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import Config
from .convert import convert_html_to_markdown
from .exclude import (
    ExclusionResult,
    TooManySelectorError,
    apply_exclusions,
    log_exclusion_errors,
    log_exclusion_warnings,
)
from .extract import ExtractionResult, extract_content_with_selectors
from .fetch import ArticleSource, fetch_html
from .logging import get_logger
from .metadata import ArticleMetadata, extract_metadata_from_html
from .naming import generate_full_path
from .timing import measure_time
from .write import create_note_file


@dataclass
class CaptureRequest:
    """Input parameters for capture operation."""

    url_or_path: str
    vault_path: Path
    config: Config
    timeout: int = 30
    max_size: int = 2_000_000
    dry_run: bool = False


@dataclass
class CaptureResult:
    """Result of successful capture operation."""

    url: str
    file_path: Path
    selector_used: str
    extracted_chars: int
    markdown_chars: int
    elapsed_ms: int
    front_matter_fields: Dict[str, Any]
    metadata: ArticleMetadata
    retrieved_at: datetime
    exclusions_applied: int = 0
    elements_excluded: int = 0
    exclusion_timing_ms: Optional[int] = None


@dataclass
class DryRunResult:
    """Result of dry run preview operation."""

    url: str
    proposed_filename: str
    selector_used: str
    extracted_chars: int
    markdown_chars: int
    elapsed_ms: int
    front_matter_fields: Dict[str, Any]
    metadata: ArticleMetadata


def capture_html_to_obsidian(
    request: CaptureRequest, start_time: Optional[float] = None
) -> Union[CaptureResult, DryRunResult]:
    """
    Orchestrate the complete HTML capture process.

    This is the main entry point that coordinates all capture steps:
    1. Fetch HTML content from URL
    2. Extract content using configured selectors
    3. Extract metadata (title, author, published date)
    4. Convert HTML fragment to Markdown
    5. Generate appropriate file path
    6. Write Markdown file with YAML front matter

    Args:
        request: Capture parameters
        start_time: Optional start time for elapsed calculation

    Returns:
        CaptureResult with all relevant information

    Raises:
        CaptureError: Structured errors for all failure modes
    """
    if start_time is None:
        import time

        start_time = time.time()

    # Import structured errors for conversion
    from .convert import ConversionError
    from .errors import ConversionError as CaptureConversionError
    from .errors import EncodingError as CaptureEncodingError
    from .errors import FetchError as CaptureFetchError
    from .errors import NoSelectorMatchError as CaptureNoSelectorMatchError
    from .errors import SizeLimitError as CaptureSizeLimitError
    from .errors import TimeoutError as CaptureTimeoutError
    from .errors import WriteError as CaptureWriteError
    from .extract import NoSelectorMatchError

    # Import module-specific errors for catching
    from .fetch import EncodingError, FetchError, SizeLimitError, TimeoutError
    from .write import WriteError

    try:
        # Step 1: Fetch HTML content (from URL or local file)
        article_source: ArticleSource = fetch_html(
            url_or_path=request.url_or_path,
            timeout=request.timeout,
            max_size=request.max_size,
        )
    except TimeoutError as e:
        raise CaptureTimeoutError(
            str(e), timeout_seconds=request.timeout, url=request.url_or_path
        ) from e
    except SizeLimitError as e:
        raise CaptureSizeLimitError(
            str(e), limit_bytes=request.max_size, url=request.url_or_path
        ) from e
    except EncodingError as e:
        raise CaptureEncodingError(str(e), url=request.url_or_path) from e
    except FetchError as e:
        raise CaptureFetchError(str(e), url=request.url_or_path) from e

    # Step 1.5: Apply exclusions if configured
    exclusion_result: Optional[ExclusionResult] = None
    exclusion_timing_ms: Optional[int] = None
    html_content = article_source.content

    if request.config.exclusion_selectors:
        from bs4 import BeautifulSoup

        logger = get_logger(__name__)

        try:
            with measure_time("exclusion", logger) as timer:
                soup = BeautifulSoup(html_content, "html.parser")
                exclusion_result = apply_exclusions(
                    soup, request.config.exclusion_selectors
                )
                html_content = str(exclusion_result.soup)

            # Capture timing information
            exclusion_timing_ms = timer.elapsed_ms()

            # Log warnings and summary with timing context
            log_exclusion_warnings(exclusion_result)

        except TooManySelectorError as e:
            # Log the error but continue without exclusions
            log_exclusion_errors(e, request.config.exclusion_selectors)
        except Exception as e:
            # Log the error but continue without exclusions
            log_exclusion_errors(e, request.config.exclusion_selectors)

    try:
        # Step 2: Extract content using selectors
        extraction_result: ExtractionResult = extract_content_with_selectors(
            html_content=html_content,
            selectors=request.config.selectors,
            min_chars=request.config.min_content_chars,
        )
    except NoSelectorMatchError as e:
        raise CaptureNoSelectorMatchError(
            str(e), selectors=request.config.selectors, url=request.url_or_path
        ) from e

    # Step 3: Extract metadata (doesn't raise specific errors currently)
    metadata: ArticleMetadata = extract_metadata_from_html(
        html_content=article_source.content, source_url=request.url_or_path
    )

    try:
        # Step 4: Convert to markdown
        markdown_content: str = convert_html_to_markdown(
            html_fragment=extraction_result.html_fragment, base_url=request.url_or_path
        )
    except ConversionError as e:
        raise CaptureConversionError(str(e), url=request.url_or_path) from e

    # Step 5: Generate file path (doesn't raise specific errors currently)
    retrieved_at = datetime.now()
    file_path: Path = generate_full_path(
        vault_path=request.vault_path,
        title=metadata.title,
        url=request.url_or_path,
        subfolder=request.config.subfolder,
        overwrite=request.config.overwrite,
        date=retrieved_at,
    )

    if request.dry_run:
        # Dry run mode: Generate front matter but don't write file
        from .write import generate_front_matter

        front_matter = generate_front_matter(
            metadata=metadata,
            config=request.config,
            url=request.url_or_path,
            selector=extraction_result.selector,
            retrieved_at=retrieved_at,
            html_content=article_source.content,
        )

        # Calculate elapsed time
        import time

        elapsed_ms = int((time.time() - start_time) * 1000)

        return DryRunResult(
            url=request.url_or_path,
            proposed_filename=file_path.name,
            selector_used=extraction_result.selector,
            extracted_chars=extraction_result.character_count,
            markdown_chars=len(markdown_content),
            elapsed_ms=elapsed_ms,
            front_matter_fields=front_matter,
            metadata=metadata,
        )

    try:
        # Step 6: Write file
        front_matter = create_note_file(
            file_path=file_path,
            metadata=metadata,
            config=request.config,
            markdown_content=markdown_content,
            url=request.url_or_path,
            selector=extraction_result.selector,
            retrieved_at=retrieved_at,
            html_content=article_source.content,
        )
    except WriteError as e:
        raise CaptureWriteError(
            str(e), file_path=str(file_path), url=request.url_or_path
        ) from e

    # Calculate elapsed time
    import time

    elapsed_ms = int((time.time() - start_time) * 1000)

    return CaptureResult(
        url=request.url_or_path,
        file_path=file_path,
        selector_used=extraction_result.selector,
        extracted_chars=extraction_result.character_count,
        markdown_chars=len(markdown_content),
        elapsed_ms=elapsed_ms,
        front_matter_fields=front_matter,
        metadata=metadata,
        retrieved_at=retrieved_at,
        exclusions_applied=exclusion_result.summary.selectors_processed
        if exclusion_result
        else 0,
        elements_excluded=exclusion_result.summary.elements_removed
        if exclusion_result
        else 0,
        exclusion_timing_ms=exclusion_timing_ms,
    )
