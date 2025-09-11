"""
Timing utilities and context managers for measuring elapsed time.

This module provides utilities for measuring operation duration
and integrating timing information with logging.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Generator, Optional


@dataclass
class TimingInfo:
    """Container for timing measurement results."""

    start_time: float
    end_time: Optional[float] = None
    elapsed_seconds: Optional[float] = None
    elapsed_ms: Optional[int] = None

    def finish(self) -> "TimingInfo":
        """Mark timing as finished and calculate elapsed time."""
        self.end_time = time.time()
        self.elapsed_seconds = self.end_time - self.start_time
        self.elapsed_ms = int(self.elapsed_seconds * 1000)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert timing info to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": self.elapsed_seconds,
            "elapsed_ms": self.elapsed_ms,
        }


class Timer:
    """Simple timer for measuring elapsed time."""

    def __init__(self) -> None:
        self.timing = TimingInfo(start_time=time.time())

    def elapsed_ms(self) -> int:
        """Get current elapsed time in milliseconds."""
        current_time = time.time()
        return int((current_time - self.timing.start_time) * 1000)

    def elapsed_seconds(self) -> float:
        """Get current elapsed time in seconds."""
        current_time = time.time()
        return current_time - self.timing.start_time

    def finish(self) -> TimingInfo:
        """Finish timing measurement and return results."""
        return self.timing.finish()


@contextmanager
def measure_time(
    operation_name: str = "operation", logger: Optional[logging.Logger] = None
) -> Generator[Timer, None, None]:
    """
    Context manager for measuring operation duration.

    Args:
        operation_name: Name of the operation being measured
        logger: Optional logger for automatic timing logs

    Yields:
        Timer instance for accessing elapsed time during operation

    Example:
        with measure_time("fetch_html") as timer:
            # Do work
            if timer.elapsed_ms() > 1000:
                print("Taking too long...")
        # timer.finish() is called automatically
    """
    timer = Timer()

    if logger:
        logger.debug(f"Starting {operation_name}")

    try:
        yield timer
    finally:
        timing_info = timer.finish()

        if logger:
            logger.info(
                f"Completed {operation_name}",
                extra={
                    "operation": operation_name,
                    "elapsed_ms": timing_info.elapsed_ms,
                    "elapsed_seconds": timing_info.elapsed_seconds,
                },
            )


@contextmanager
def capture_timing() -> Generator[Timer, None, None]:
    """
    Simple context manager for capturing timing without logging.

    Yields:
        Timer instance that can be used to access timing information

    Example:
        with capture_timing() as timer:
            # Do work
            pass
        print(f"Operation took {timer.elapsed_ms()}ms")
    """
    timer = Timer()
    try:
        yield timer
    finally:
        timer.finish()


def log_timing_context(
    timing_info: TimingInfo, context: Dict[str, Any], logger: logging.Logger
) -> None:
    """
    Log timing information with additional context.

    Args:
        timing_info: Timing measurement results
        context: Additional context to include in log
        logger: Logger instance to use
    """
    log_data = {**timing_info.to_dict(), **context}

    logger.info(f"Operation completed in {timing_info.elapsed_ms}ms", extra=log_data)
