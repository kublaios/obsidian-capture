"""Unit tests for selector validation and protected roots exclusion logic."""

from src.obsidian_capture.exclude import (
    is_protected_selector,
    validate_selectors,
)


class TestSelectorValidation:
    """Test CSS selector validation functionality."""

    def test_valid_css_selectors(self):
        """Test that valid CSS selectors pass validation."""
        valid_selectors = [
            "div.footer",
            ".advertisement",
            "#sidebar",
            "nav.breadcrumb",
            "article .content",
            "section[role='complementary']",
            "footer, .footer",
        ]

        for selector in valid_selectors:
            result = validate_selectors([selector])
            assert len(result.valid) == 1
            assert len(result.invalid) == 0
            assert result.valid[0].selector == selector

    def test_invalid_css_selectors(self):
        """Test that invalid CSS selectors are caught."""
        invalid_selectors = [
            "div[unclosed",
            "::invalid-pseudo",
            ">>invalid",
            ".class{invalid}",
            "",
            None,
        ]

        for selector in invalid_selectors:
            if selector is not None:
                result = validate_selectors([selector])
                assert len(result.invalid) >= 1
                assert selector in [s.selector for s in result.invalid]

    def test_mixed_valid_invalid_selectors(self):
        """Test validation with mix of valid and invalid selectors."""
        selectors = [
            "div.footer",  # valid
            "div[unclosed",  # invalid
            ".advertisement",  # valid
            "::invalid-pseudo",  # invalid
        ]

        result = validate_selectors(selectors)
        assert len(result.valid) == 2
        assert len(result.invalid) == 2

        valid_selectors = [s.selector for s in result.valid]
        invalid_selectors = [s.selector for s in result.invalid]

        assert "div.footer" in valid_selectors
        assert ".advertisement" in valid_selectors
        assert "div[unclosed" in invalid_selectors
        assert "::invalid-pseudo" in invalid_selectors


class TestProtectedRootSelectors:
    """Test protected root selector detection."""

    def test_html_selector_is_protected(self):
        """Test that 'html' selector is protected."""
        assert is_protected_selector("html") is True
        assert is_protected_selector("html *") is True
        assert is_protected_selector("html.some-class") is True

    def test_body_selector_is_protected(self):
        """Test that 'body' selector is protected."""
        assert is_protected_selector("body") is True
        assert is_protected_selector("body *") is True
        assert is_protected_selector("body.main") is True

    def test_non_protected_selectors(self):
        """Test that non-protected selectors are not flagged."""
        non_protected = [
            "div.footer",
            ".advertisement",
            "#sidebar",
            "nav",
            "article",
            "section[role='complementary']",
            "header, footer",
        ]

        for selector in non_protected:
            assert is_protected_selector(selector) is False

    def test_protected_selector_validation(self):
        """Test that protected selectors are filtered out during validation."""
        selectors = [
            "html",  # protected
            "div.footer",  # valid
            "body",  # protected
            ".advertisement",  # valid
        ]

        result = validate_selectors(selectors)

        # Protected selectors should be moved to invalid
        valid_selectors = [s.selector for s in result.valid]
        invalid_selectors = [s.selector for s in result.invalid]

        assert "div.footer" in valid_selectors
        assert ".advertisement" in valid_selectors
        assert "html" in invalid_selectors
        assert "body" in invalid_selectors

        # Check that protected selectors have appropriate error reason
        html_error = next(s for s in result.invalid if s.selector == "html")
        body_error = next(s for s in result.invalid if s.selector == "body")

        assert "protected" in html_error.reason.lower()
        assert "protected" in body_error.reason.lower()

    def test_empty_selector_list(self):
        """Test validation with empty selector list."""
        result = validate_selectors([])
        assert len(result.valid) == 0
        assert len(result.invalid) == 0
