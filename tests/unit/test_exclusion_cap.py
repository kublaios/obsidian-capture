"""Unit tests for selector cap enforcement (>100 selectors limit)."""

import pytest
from src.obsidian_capture.exclude import (
    TooManySelectorError,
    validate_selectors,
)


class TestSelectorCapEnforcement:
    """Test enforcement of selector count limits."""

    def test_selector_count_under_limit(self):
        """Test that selector counts under 100 are accepted."""
        selectors = [f".class-{i}" for i in range(99)]
        result = validate_selectors(selectors)

        assert len(result.valid) == 99
        assert len(result.invalid) == 0
        assert result.total_count == 99
        assert result.cap_exceeded is False

    def test_selector_count_at_limit(self):
        """Test that exactly 100 selectors are accepted."""
        selectors = [f".class-{i}" for i in range(100)]
        result = validate_selectors(selectors)

        assert len(result.valid) == 100
        assert len(result.invalid) == 0
        assert result.total_count == 100
        assert result.cap_exceeded is False

    def test_selector_count_over_limit_raises_error(self):
        """Test that over 100 selectors raises TooManySelectorError."""
        selectors = [f".class-{i}" for i in range(101)]

        with pytest.raises(TooManySelectorError) as exc_info:
            validate_selectors(selectors)

        assert "100" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_selector_count_way_over_limit_raises_error(self):
        """Test that way over 100 selectors raises TooManySelectorError."""
        selectors = [f".class-{i}" for i in range(200)]

        with pytest.raises(TooManySelectorError) as exc_info:
            validate_selectors(selectors)

        assert "100" in str(exc_info.value)
        assert "200" in str(exc_info.value)

    def test_duplicate_selectors_count_towards_limit(self):
        """Test that duplicate selectors count towards the limit."""
        # Create 101 selectors with duplicates
        selectors = [".footer"] * 101

        with pytest.raises(TooManySelectorError):
            validate_selectors(selectors)

    def test_invalid_selectors_count_towards_limit(self):
        """Test that invalid selectors still count towards the limit."""
        # Mix of valid and invalid selectors totaling 101
        valid_selectors = [f".class-{i}" for i in range(50)]
        invalid_selectors = [f"div[unclosed-{i}" for i in range(51)]  # Invalid CSS
        all_selectors = valid_selectors + invalid_selectors

        with pytest.raises(TooManySelectorError):
            validate_selectors(all_selectors)

    def test_empty_list_does_not_exceed_cap(self):
        """Test that empty selector list does not trigger cap error."""
        result = validate_selectors([])

        assert len(result.valid) == 0
        assert len(result.invalid) == 0
        assert result.total_count == 0
        assert result.cap_exceeded is False

    def test_single_selector_does_not_exceed_cap(self):
        """Test that single selector does not trigger cap error."""
        result = validate_selectors([".footer"])

        assert len(result.valid) == 1
        assert len(result.invalid) == 0
        assert result.total_count == 1
        assert result.cap_exceeded is False

    def test_cap_error_message_includes_counts(self):
        """Test that cap error message includes actual and limit counts."""
        selectors = [f".class-{i}" for i in range(150)]

        with pytest.raises(TooManySelectorError) as exc_info:
            validate_selectors(selectors)

        error_message = str(exc_info.value)
        assert "150" in error_message  # actual count
        assert "100" in error_message  # limit
        assert "selector" in error_message.lower()
        assert "limit" in error_message.lower()

    def test_protected_selectors_count_towards_limit(self):
        """Test that protected selectors (html, body) still count towards limit."""
        # 99 valid + 1 protected + 1 more valid = 101 total
        selectors = [f".class-{i}" for i in range(99)] + ["html"] + [".one-more"]

        with pytest.raises(TooManySelectorError):
            validate_selectors(selectors)
