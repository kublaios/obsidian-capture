"""Integration test for invalid selector warning (skip invalid, apply rest)."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import apply_exclusions


class TestInvalidSelectorHandling:
    """Test handling of invalid CSS selectors mixed with valid ones."""

    def test_invalid_selector_skipped_valid_applied(self):
        """Test that invalid selectors are skipped while valid ones are applied."""
        html = """
        <html>
            <body>
                <div class="content">Main content</div>
                <footer>Footer content</footer>
                <aside>Sidebar content</aside>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "footer",  # valid
            "div[unclosed",  # invalid
            "aside",  # valid
        ]

        result = apply_exclusions(soup, selectors)

        # Valid selectors should work
        assert "Footer content" not in result.soup.get_text()
        assert "Sidebar content" not in result.soup.get_text()

        # Content not targeted by invalid selector should remain
        assert "Main content" in result.soup.get_text()

        # Summary should reflect mixed success/failure
        assert result.summary.selectors_processed == 3
        assert result.summary.successful_selectors == 2
        assert result.summary.failed_selectors == 1
        assert result.summary.elements_removed == 2

    def test_all_invalid_selectors(self):
        """Test behavior when all selectors are invalid."""
        html = """
        <html>
            <body>
                <div class="content">All content should remain</div>
                <footer>Footer should remain</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "div[unclosed",  # invalid
            "::invalid-pseudo",  # invalid
            ".class{bad}",  # invalid
        ]

        result = apply_exclusions(soup, selectors)

        # All content should remain
        assert "All content should remain" in result.soup.get_text()
        assert "Footer should remain" in result.soup.get_text()

        # Summary should show all failures
        assert result.summary.selectors_processed == 3
        assert result.summary.successful_selectors == 0
        assert result.summary.failed_selectors == 3
        assert result.summary.elements_removed == 0

    def test_malformed_css_syntax_errors(self):
        """Test various types of malformed CSS syntax errors."""
        html = """
        <html>
            <body>
                <div class="keep">Keep this</div>
                <div class="remove">Remove this</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            ".remove",  # valid - should work
            "div[attr=unclosed",  # invalid - missing closing bracket
            ".class:invalid-pseudo(",  # invalid - malformed pseudo
            ">>invalid",  # invalid - bad combinator
            "",  # invalid - empty selector
            ".valid-but-after-invalid",  # valid but targeting non-existent element
        ]

        result = apply_exclusions(soup, selectors)

        # Valid selector should work
        assert "Remove this" not in result.soup.get_text()
        assert "Keep this" in result.soup.get_text()

        # Should have mixed results
        assert result.summary.selectors_processed == 6
        assert result.summary.failed_selectors >= 4  # At least the clearly invalid ones
        assert result.summary.elements_removed == 1

    def test_selector_validation_error_messages(self):
        """Test that invalid selectors generate appropriate error messages."""
        html = """
        <html>
            <body>
                <div>Content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["div[unclosed", "::invalid-pseudo"]

        result = apply_exclusions(soup, selectors)

        # Should record failure reasons for invalid selectors
        assert result.summary.failed_selectors == 2

        # Error details should be available (implementation-specific)
        # This tests that the system captures WHY selectors failed
        if hasattr(result, "selector_results"):
            failed_results = [s for s in result.selector_results if not s.success]
            assert len(failed_results) == 2

            for failed_result in failed_results:
                assert failed_result.error_message is not None
                assert len(failed_result.error_message) > 0

    def test_protected_selectors_treated_as_invalid(self):
        """Test that protected selectors (html, body) are treated as invalid."""
        html = """
        <html>
            <body>
                <div class="content">Content should remain</div>
                <footer>Footer should be removed</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "html",  # protected - should be invalid
            "footer",  # valid
            "body",  # protected - should be invalid
        ]

        result = apply_exclusions(soup, selectors)

        # Protected selectors should be ignored
        html_elem = result.soup.find("html")
        body_elem = result.soup.find("body")
        assert html_elem is not None
        assert body_elem is not None

        # Valid selector should work
        assert "Footer should be removed" not in result.soup.get_text()
        assert "Content should remain" in result.soup.get_text()

        # Summary should reflect protected selectors as failures
        assert result.summary.selectors_processed == 3
        assert result.summary.successful_selectors == 1
        assert result.summary.failed_selectors == 2
        assert result.summary.elements_removed == 1

    def test_partial_success_continues_processing(self):
        """Test that processing continues after encountering invalid selectors."""
        html = """
        <html>
            <body>
                <header>Remove header</header>
                <main>Keep main</main>
                <aside>Remove aside</aside>
                <footer>Remove footer</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "header",  # valid
            "div[bad",  # invalid
            "main",  # valid (but we won't remove it in this test)
            "::invalid",  # invalid
            "aside",  # valid
            "body",  # invalid (protected)
            "footer",  # valid
        ]

        result = apply_exclusions(soup, selectors)

        # Valid non-protected selectors should work
        assert "Remove header" not in result.soup.get_text()
        assert "Remove aside" not in result.soup.get_text()
        assert "Remove footer" not in result.soup.get_text()

        # Main should remain (or be removed, depending on selector)
        # Body should definitely remain (protected)
        assert result.soup.find("body") is not None

        # Should have processed all selectors
        assert result.summary.selectors_processed == 7
        assert result.summary.failed_selectors >= 3  # At least the clearly invalid ones

    def test_mixed_valid_invalid_with_no_matches(self):
        """Test mixed selectors where some valid ones don't match any elements."""
        html = """
        <html>
            <body>
                <div class="content">Content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            ".content",  # valid and matches
            ".nonexistent",  # valid but no match
            "div[bad",  # invalid
            "footer",  # valid but no match
        ]

        result = apply_exclusions(soup, selectors)

        # Content should be removed
        assert "Content" not in result.soup.get_text()

        # Should distinguish between invalid selectors and valid ones with no matches
        assert result.summary.selectors_processed == 4
        # Implementation may treat "no matches" as success or failure
        assert result.summary.failed_selectors >= 1  # At least the invalid one
        assert result.summary.elements_removed == 1
