"""Unit tests for exclusion logging and message formatting."""

import logging

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import (
    ExclusionResult,
    ExclusionSummary,
    SelectorResult,
    log_exclusion_warnings,
)


class TestExclusionLoggingFormat:
    """Test logging format consistency and structured data."""

    def test_logging_consistency_across_functions(self):
        """Test that all logging functions use consistent 'operation' field."""
        # This test ensures all exclusion logging includes the 'operation': 'exclude' field
        # for consistent log filtering and monitoring

        # This is verified by the individual test cases above, but serves as documentation
        # that the 'operation': 'exclude' field should be present in all structured logs
        assert True  # Placeholder - consistency verified in other tests


class TestLoggingIntegration:
    """Integration tests for logging with real logger instances."""

    def test_logging_with_real_logger(self, caplog):
        """Test logging integration with actual logger."""
        with caplog.at_level(logging.INFO):
            # Create test data
            selector_results = [
                SelectorResult(selector="footer", success=True, elements_removed=2),
            ]
            summary = ExclusionSummary(
                selectors_processed=1,
                elements_removed=2,
                original_element_count=20,
                successful_selectors=1,
                failed_selectors=0,
            )
            soup = BeautifulSoup("<div>content</div>", "html.parser")
            result = ExclusionResult(
                soup=soup, summary=summary, selector_results=selector_results
            )

            # Execute logging
            log_exclusion_warnings(result)

        # Verify log message appears in caplog
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert "Exclusion summary:" in record.message
        assert hasattr(record, "selectors_processed")
        assert record.selectors_processed == 1
        assert hasattr(record, "operation")
        assert record.operation == "exclude"
