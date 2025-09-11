"""
Structured error classes for Obsidian Capture.

This module defines all error types used throughout the application
and their mapping to CLI exit codes for consistent error handling.
"""

from typing import Any, Dict, Optional


class CaptureError(Exception):
    """Base exception for HTML capture operations."""

    def __init__(self, message: str, code: str, exit_code: int, **context: Any) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        result = {
            "status": "error",
            "message": str(self),
            "code": self.code,
            **self.context,
        }
        return result


class ConfigError(CaptureError):
    """Configuration-related errors (invalid arguments, missing files, etc.)."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message, "CONFIG_ERROR", 9, **context)


class NoSelectorMatchError(CaptureError):
    """No configured selector successfully extracted content."""

    def __init__(
        self, message: str, selectors: Optional[list[str]] = None, **context: Any
    ) -> None:
        if selectors:
            context["selector_attempts"] = selectors
        super().__init__(message, "NO_SELECTOR_MATCH", 2, **context)


class TimeoutError(CaptureError):
    """Network request timed out."""

    def __init__(
        self, message: str, timeout_seconds: Optional[int] = None, **context: Any
    ) -> None:
        if timeout_seconds:
            context["timeout_seconds"] = timeout_seconds
        super().__init__(message, "TIMEOUT", 3, **context)


class SizeLimitError(CaptureError):
    """Content exceeds maximum size limit."""

    def __init__(
        self,
        message: str,
        size_bytes: Optional[int] = None,
        limit_bytes: Optional[int] = None,
        **context: Any,
    ) -> None:
        if size_bytes:
            context["size_bytes"] = size_bytes
        if limit_bytes:
            context["limit_bytes"] = limit_bytes
        super().__init__(message, "SIZE_LIMIT", 4, **context)


class EncodingError(CaptureError):
    """Character encoding issues during fetch/decode."""

    def __init__(
        self, message: str, encoding: Optional[str] = None, **context: Any
    ) -> None:
        if encoding:
            context["encoding"] = encoding
        super().__init__(message, "ENCODING_ERROR", 5, **context)


class FetchError(CaptureError):
    """Generic HTTP fetch failures."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, **context: Any
    ) -> None:
        if status_code:
            context["status_code"] = status_code
        super().__init__(message, "FETCH_ERROR", 6, **context)


class ConversionError(CaptureError):
    """HTML to Markdown conversion failures."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message, "CONVERSION_ERROR", 7, **context)


class WriteError(CaptureError):
    """File system write failures."""

    def __init__(
        self, message: str, file_path: Optional[str] = None, **context: Any
    ) -> None:
        if file_path:
            context["file_path"] = file_path
        super().__init__(message, "WRITE_ERROR", 8, **context)


class ImportError(CaptureError):
    """Module import failures."""

    def __init__(
        self, message: str, module_name: Optional[str] = None, **context: Any
    ) -> None:
        if module_name:
            context["module_name"] = module_name
        super().__init__(message, "IMPORT_ERROR", 1, **context)


class GenericError(CaptureError):
    """Catch-all for unexpected errors."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message, "GENERIC_ERROR", 1, **context)


# Exit code mapping for backwards compatibility
EXIT_CODES = {
    "GENERIC_ERROR": 1,
    "IMPORT_ERROR": 1,
    "NO_SELECTOR_MATCH": 2,
    "TIMEOUT": 3,
    "SIZE_LIMIT": 4,
    "ENCODING_ERROR": 5,
    "FETCH_ERROR": 6,
    "CONVERSION_ERROR": 7,
    "WRITE_ERROR": 8,
    "CONFIG_ERROR": 9,
}


def get_exit_code(error_code: str) -> int:
    """Get CLI exit code for error code string."""
    return EXIT_CODES.get(error_code, 1)
