"""Unit tests for summary aggregation (counts, ratio, flags)."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import (
    ExclusionSummary,
    SelectorResult,
    aggregate_exclusion_summary,
)


class TestExclusionSummary:
    """Test ExclusionSummary data structure and calculations."""

    def test_summary_basic_properties(self):
        """Test basic ExclusionSummary properties."""
        summary = ExclusionSummary(
            selectors_processed=5,
            elements_removed=25,
            original_element_count=100,
            successful_selectors=4,
            failed_selectors=1,
        )

        assert summary.selectors_processed == 5
        assert summary.elements_removed == 25
        assert summary.original_element_count == 100
        assert summary.successful_selectors == 4
        assert summary.failed_selectors == 1

    def test_summary_removal_ratio_calculation(self):
        """Test removal ratio calculation."""
        summary = ExclusionSummary(
            selectors_processed=3,
            elements_removed=30,
            original_element_count=100,
            successful_selectors=3,
            failed_selectors=0,
        )

        assert summary.removal_ratio == 0.3

    def test_summary_high_removal_warning_flag(self):
        """Test high removal warning flag calculation."""
        # Below threshold
        summary_low = ExclusionSummary(
            selectors_processed=2,
            elements_removed=20,
            original_element_count=100,
            successful_selectors=2,
            failed_selectors=0,
        )
        assert summary_low.high_removal_warning is False

        # Above threshold
        summary_high = ExclusionSummary(
            selectors_processed=2,
            elements_removed=50,
            original_element_count=100,
            successful_selectors=2,
            failed_selectors=0,
        )
        assert summary_high.high_removal_warning is True

    def test_summary_zero_original_elements(self):
        """Test summary with zero original elements."""
        summary = ExclusionSummary(
            selectors_processed=3,
            elements_removed=0,
            original_element_count=0,
            successful_selectors=0,
            failed_selectors=3,
        )

        assert summary.removal_ratio == 0.0
        assert summary.high_removal_warning is False

    def test_summary_no_elements_removed(self):
        """Test summary with no elements removed."""
        summary = ExclusionSummary(
            selectors_processed=3,
            elements_removed=0,
            original_element_count=100,
            successful_selectors=0,
            failed_selectors=3,
        )

        assert summary.removal_ratio == 0.0
        assert summary.high_removal_warning is False

    def test_summary_complete_removal(self):
        """Test summary with complete removal."""
        summary = ExclusionSummary(
            selectors_processed=2,
            elements_removed=50,
            original_element_count=50,
            successful_selectors=2,
            failed_selectors=0,
        )

        assert summary.removal_ratio == 1.0
        assert summary.high_removal_warning is True


class TestSelectorResult:
    """Test SelectorResult data structure."""

    def test_successful_selector_result(self):
        """Test successful selector result."""
        result = SelectorResult(
            selector=".footer", success=True, elements_removed=5, error_message=None
        )

        assert result.selector == ".footer"
        assert result.success is True
        assert result.elements_removed == 5
        assert result.error_message is None

    def test_failed_selector_result(self):
        """Test failed selector result."""
        result = SelectorResult(
            selector="div[unclosed",
            success=False,
            elements_removed=0,
            error_message="Invalid CSS selector syntax",
        )

        assert result.selector == "div[unclosed"
        assert result.success is False
        assert result.elements_removed == 0
        assert result.error_message == "Invalid CSS selector syntax"


class TestAggregateExclusionSummary:
    """Test aggregation of exclusion results into summary."""

    def _create_mock_soup_with_content(self):
        """Create mock soup with some remaining content."""
        return BeautifulSoup("<article>Some content</article>", "html.parser")

    def test_aggregate_all_successful_selectors(self):
        """Test aggregation with all successful selectors."""
        selector_results = [
            SelectorResult(".footer", True, 3, None),
            SelectorResult(".advertisement", True, 7, None),
            SelectorResult("#sidebar", True, 2, None),
        ]

        original_count = 100
        soup = self._create_mock_soup_with_content()
        summary = aggregate_exclusion_summary(selector_results, original_count, soup)

        assert summary.selectors_processed == 3
        assert summary.successful_selectors == 3
        assert summary.failed_selectors == 0
        assert summary.elements_removed == 12  # 3 + 7 + 2
        assert summary.original_element_count == 100
        assert summary.removal_ratio == 0.12

    def test_aggregate_mixed_success_failure(self):
        """Test aggregation with mixed successful and failed selectors."""
        selector_results = [
            SelectorResult(".footer", True, 5, None),
            SelectorResult("div[unclosed", False, 0, "Invalid syntax"),
            SelectorResult(".ad", True, 10, None),
            SelectorResult("html", False, 0, "Protected selector"),
        ]

        original_count = 200
        soup = self._create_mock_soup_with_content()
        summary = aggregate_exclusion_summary(selector_results, original_count, soup)

        assert summary.selectors_processed == 4
        assert summary.successful_selectors == 2
        assert summary.failed_selectors == 2
        assert summary.elements_removed == 15  # 5 + 0 + 10 + 0
        assert summary.original_element_count == 200
        assert summary.removal_ratio == 0.075

    def test_aggregate_all_failed_selectors(self):
        """Test aggregation with all failed selectors."""
        selector_results = [
            SelectorResult("div[unclosed", False, 0, "Invalid syntax"),
            SelectorResult("html", False, 0, "Protected selector"),
            SelectorResult("body", False, 0, "Protected selector"),
        ]

        original_count = 150
        soup = self._create_mock_soup_with_content()
        summary = aggregate_exclusion_summary(selector_results, original_count, soup)

        assert summary.selectors_processed == 3
        assert summary.successful_selectors == 0
        assert summary.failed_selectors == 3
        assert summary.elements_removed == 0
        assert summary.original_element_count == 150
        assert summary.removal_ratio == 0.0
        assert summary.high_removal_warning is False

    def test_aggregate_high_removal_triggers_warning(self):
        """Test aggregation that triggers high removal warning."""
        selector_results = [
            SelectorResult(".content", True, 45, None),
            SelectorResult(".main", True, 5, None),
        ]

        original_count = 100
        soup = self._create_mock_soup_with_content()
        summary = aggregate_exclusion_summary(selector_results, original_count, soup)

        assert summary.selectors_processed == 2
        assert summary.successful_selectors == 2
        assert summary.failed_selectors == 0
        assert summary.elements_removed == 50
        assert summary.removal_ratio == 0.5
        assert summary.high_removal_warning is True

    def test_aggregate_empty_selector_results(self):
        """Test aggregation with empty selector results."""
        selector_results = []
        original_count = 100
        soup = self._create_mock_soup_with_content()

        summary = aggregate_exclusion_summary(selector_results, original_count, soup)

        assert summary.selectors_processed == 0
        assert summary.successful_selectors == 0
        assert summary.failed_selectors == 0
        assert summary.elements_removed == 0
        assert summary.original_element_count == 100
        assert summary.removal_ratio == 0.0
        assert summary.high_removal_warning is False

    def test_aggregate_zero_original_elements(self):
        """Test aggregation with zero original elements."""
        selector_results = [
            SelectorResult(".footer", False, 0, "No elements found"),
        ]

        original_count = 0
        soup = self._create_mock_soup_with_content()
        summary = aggregate_exclusion_summary(selector_results, original_count, soup)

        assert summary.selectors_processed == 1
        assert summary.successful_selectors == 0
        assert summary.failed_selectors == 1
        assert summary.elements_removed == 0
        assert summary.original_element_count == 0
        assert summary.removal_ratio == 0.0
        assert summary.high_removal_warning is False
