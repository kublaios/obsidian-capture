"""Unit tests for high removal warning threshold logic."""

from src.obsidian_capture.exclude import (
    ExclusionSummary,
    calculate_removal_ratio,
    should_warn_high_removal,
)


class TestHighRemovalThresholds:
    """Test high removal warning threshold detection."""

    def test_low_removal_ratio_no_warning(self):
        """Test that low removal ratios don't trigger warnings."""
        # 10% removal - well below 40% threshold
        original_elements = 100
        removed_elements = 10

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.1
        assert should_warn is False

    def test_moderate_removal_ratio_no_warning(self):
        """Test that moderate removal ratios don't trigger warnings."""
        # 35% removal - below 40% threshold
        original_elements = 100
        removed_elements = 35

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.35
        assert should_warn is False

    def test_exactly_at_threshold_triggers_warning(self):
        """Test that exactly 40% removal triggers warning."""
        original_elements = 100
        removed_elements = 40

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.4
        assert should_warn is True

    def test_above_threshold_triggers_warning(self):
        """Test that above 40% removal triggers warning."""
        # 60% removal - well above 40% threshold
        original_elements = 100
        removed_elements = 60

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.6
        assert should_warn is True

    def test_high_removal_ratio_triggers_warning(self):
        """Test that high removal ratios trigger warnings."""
        # 90% removal - very high
        original_elements = 100
        removed_elements = 90

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.9
        assert should_warn is True

    def test_complete_removal_triggers_warning(self):
        """Test that 100% removal triggers warning."""
        original_elements = 50
        removed_elements = 50

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 1.0
        assert should_warn is True

    def test_zero_original_elements_no_warning(self):
        """Test that zero original elements doesn't trigger warning."""
        original_elements = 0
        removed_elements = 0

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.0
        assert should_warn is False

    def test_zero_removed_elements_no_warning(self):
        """Test that zero removed elements doesn't trigger warning."""
        original_elements = 100
        removed_elements = 0

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert ratio == 0.0
        assert should_warn is False

    def test_fractional_elements_above_threshold(self):
        """Test threshold calculation with fractional results."""
        # 7 out of 17 elements = ~41.2% removal
        original_elements = 17
        removed_elements = 7

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert abs(ratio - 0.4118) < 0.001  # approximately 41.18%
        assert should_warn is True

    def test_fractional_elements_below_threshold(self):
        """Test threshold calculation with fractional results below threshold."""
        # 6 out of 17 elements = ~35.3% removal
        original_elements = 17
        removed_elements = 6

        ratio = calculate_removal_ratio(removed_elements, original_elements)
        should_warn = should_warn_high_removal(ratio)

        assert abs(ratio - 0.353) < 0.001  # approximately 35.29%
        assert should_warn is False


class TestExclusionSummaryThresholds:
    """Test ExclusionSummary integration with threshold logic."""

    def test_summary_flags_high_removal(self):
        """Test that ExclusionSummary correctly flags high removal."""
        summary = ExclusionSummary(
            selectors_processed=3,
            elements_removed=45,
            original_element_count=100,
            successful_selectors=3,
            failed_selectors=0,
        )

        assert summary.removal_ratio == 0.45
        assert summary.high_removal_warning is True

    def test_summary_no_flag_low_removal(self):
        """Test that ExclusionSummary doesn't flag low removal."""
        summary = ExclusionSummary(
            selectors_processed=3,
            elements_removed=25,
            original_element_count=100,
            successful_selectors=3,
            failed_selectors=0,
        )

        assert summary.removal_ratio == 0.25
        assert summary.high_removal_warning is False

    def test_summary_edge_case_exactly_threshold(self):
        """Test ExclusionSummary at exactly the threshold."""
        summary = ExclusionSummary(
            selectors_processed=2,
            elements_removed=20,
            original_element_count=50,
            successful_selectors=2,
            failed_selectors=0,
        )

        assert summary.removal_ratio == 0.4
        assert summary.high_removal_warning is True
