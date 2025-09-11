"""HTTP fetching with timeout and size limits."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout


class FetchError(Exception):
    """HTTP fetch related error."""

    pass


class TimeoutError(FetchError):
    """Request timeout error."""

    pass


class SizeLimitError(FetchError):
    """Content size limit exceeded error."""

    pass


class EncodingError(FetchError):
    """Content encoding/decoding error."""

    pass


@dataclass
class ArticleSource:
    """Container for fetched article source and metadata."""

    url: str
    content: str
    encoding: str
    content_type: str
    status_code: int
    elapsed_seconds: float
    raw_size_bytes: int


def _is_url(url_or_path: str) -> bool:
    """Check if the input string is a URL or a local file path."""
    try:
        parsed = urlparse(url_or_path)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False


def _read_local_file(file_path: str, max_size: int) -> ArticleSource:
    """Read HTML content from a local file."""
    start_time = time.time()

    try:
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            raise FetchError(f"File does not exist: {file_path}")

        # Check if it's a file (not a directory)
        if not path.is_file():
            raise FetchError(f"Path is not a file: {file_path}")

        # Check file size before reading
        file_size = path.stat().st_size
        if file_size > max_size:
            raise SizeLimitError(
                f"File size {file_size} bytes exceeds limit {max_size} bytes"
            )

        # Read file content
        try:
            # Try UTF-8 first, then fallback to other encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    content = path.read_text(encoding=encoding)
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise EncodingError(
                    f"Failed to decode file with any common encoding: {file_path}"
                )

        except Exception as e:
            if isinstance(e, (EncodingError, UnicodeDecodeError)):
                raise
            raise FetchError(f"Failed to read file: {e}") from e

        elapsed_seconds = time.time() - start_time

        return ArticleSource(
            url=file_path,
            content=content,
            encoding=used_encoding,
            content_type="text/html",
            status_code=200,  # Simulate successful HTTP status
            elapsed_seconds=elapsed_seconds,
            raw_size_bytes=file_size,
        )

    except Exception as e:
        if isinstance(e, (FetchError, SizeLimitError, EncodingError)):
            raise
        raise FetchError(f"Unexpected error reading file {file_path}: {e}") from e


def fetch_html(
    url_or_path: str,
    timeout: int = 30,
    max_size: int = 2000000,
    user_agent: Optional[str] = None,
) -> ArticleSource:
    """
    Fetch HTML content from URL or read from local file with size limits.

    Args:
        url_or_path: URL to fetch or local file path to read
        timeout: Request timeout in seconds (ignored for local files)
        max_size: Maximum content size in bytes
        user_agent: Optional user agent string (ignored for local files)

    Returns:
        ArticleSource with content and metadata

    Raises:
        FetchError: For HTTP/network errors or file read errors
        TimeoutError: For request timeouts
        SizeLimitError: For oversized content
        EncodingError: For encoding/decoding issues
    """
    # Check if input is a URL or a local file path
    if _is_url(url_or_path):
        return _fetch_from_url(url_or_path, timeout, max_size, user_agent)
    else:
        return _read_local_file(url_or_path, max_size)


def _fetch_from_url(
    url: str, timeout: int, max_size: int, user_agent: Optional[str]
) -> ArticleSource:
    """Fetch HTML content from a URL."""
    if not user_agent:
        user_agent = "Mozilla/5.0 (compatible; Obsidian-Capture/1.0; +https://github.com/mkerddev/obsidian-capture)"

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    start_time = time.time()

    try:
        # Make request with streaming to check size before downloading full content
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)

        # Check status code
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get("content-type", "").lower()
        if not any(
            ct in content_type
            for ct in ["text/html", "application/xhtml", "application/xml"]
        ):
            # Still allow, but note it might not be HTML
            pass

        # Check content length if provided
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                content_length_int = int(content_length)
                if content_length_int > max_size:
                    response.close()
                    raise SizeLimitError(
                        f"Content size {content_length_int} bytes exceeds limit {max_size} bytes"
                    )
            except ValueError:
                # Invalid content-length header, proceed with streaming check
                pass

        # Download content in chunks, checking size
        content_bytes = b""
        for chunk in response.iter_content(chunk_size=8192):
            content_bytes += chunk
            if len(content_bytes) > max_size:
                response.close()
                raise SizeLimitError(f"Content size exceeds limit {max_size} bytes")

        elapsed_seconds = time.time() - start_time
        raw_size_bytes = len(content_bytes)

        # Decode content
        encoding = response.encoding or "utf-8"
        try:
            content = content_bytes.decode(encoding)
        except UnicodeDecodeError:
            # Try common encodings as fallback
            for fallback_encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    content = content_bytes.decode(fallback_encoding)
                    encoding = fallback_encoding
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise EncodingError(
                    f"Failed to decode content with encoding {encoding}"
                )

        return ArticleSource(
            url=url,
            content=content,
            encoding=encoding,
            content_type=content_type,
            status_code=response.status_code,
            elapsed_seconds=elapsed_seconds,
            raw_size_bytes=raw_size_bytes,
        )

    except Timeout:
        raise TimeoutError(f"Request timed out after {timeout} seconds") from None

    except ConnectionError as e:
        raise FetchError(f"Connection failed: {e}") from e

    except requests.HTTPError as e:
        raise FetchError(f"HTTP error {e.response.status_code}: {e}") from e

    except RequestException as e:
        raise FetchError(f"Request failed: {e}") from e

    except Exception as e:
        raise FetchError(f"Unexpected error during fetch: {e}") from e
