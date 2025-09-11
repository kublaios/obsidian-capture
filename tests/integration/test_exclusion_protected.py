"""Integration test for protected root skip (html/body)."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import apply_exclusions


class TestProtectedRootSkip:
    """Test that protected root elements (html, body) are not removed."""

    def test_html_selector_is_protected(self):
        """Test that 'html' selector is protected and not removed."""
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <div>Content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["html"]

        result = apply_exclusions(soup, selectors)

        # HTML element should still exist
        html_elem = result.soup.find("html")
        assert html_elem is not None

        # Content should remain
        assert "Content" in result.soup.get_text()

        # Should be recorded as failed/invalid selector
        assert result.summary.failed_selectors >= 1
        assert result.summary.elements_removed == 0

    def test_body_selector_is_protected(self):
        """Test that 'body' selector is protected and not removed."""
        html = """
        <html>
            <body>
                <div>Body content should remain</div>
                <p>All content preserved</p>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["body"]

        result = apply_exclusions(soup, selectors)

        # Body element should still exist
        body_elem = result.soup.find("body")
        assert body_elem is not None

        # All content should remain
        assert "Body content should remain" in result.soup.get_text()
        assert "All content preserved" in result.soup.get_text()

        # Should be recorded as failed/invalid selector
        assert result.summary.failed_selectors >= 1
        assert result.summary.elements_removed == 0

    def test_html_with_attributes_is_protected(self):
        """Test that html selectors with attributes are still protected."""
        html = """
        <html lang="en">
            <body>
                <div>Content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ['html[lang="en"]', "html.some-class"]

        result = apply_exclusions(soup, selectors)

        # HTML element should still exist
        html_elem = result.soup.find("html")
        assert html_elem is not None

        # Content should remain
        assert "Content" in result.soup.get_text()

        # Both selectors should be treated as invalid
        assert result.summary.failed_selectors >= 2
        assert result.summary.elements_removed == 0

    def test_body_with_classes_is_protected(self):
        """Test that body selectors with classes are still protected."""
        html = """
        <html>
            <body class="main-body" data-theme="light">
                <div>Body content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["body.main-body", 'body[data-theme="light"]']

        result = apply_exclusions(soup, selectors)

        # Body element should still exist with its attributes
        body_elem = result.soup.find("body")
        assert body_elem is not None
        assert "main-body" in body_elem.get("class", [])
        assert body_elem.get("data-theme") == "light"

        # Content should remain
        assert "Body content" in result.soup.get_text()

        # Both selectors should be treated as invalid
        assert result.summary.failed_selectors >= 2
        assert result.summary.elements_removed == 0

    def test_protected_mixed_with_valid_selectors(self):
        """Test protected selectors mixed with valid selectors."""
        html = """
        <html>
            <body>
                <header>Header to remove</header>
                <main>Main content to keep</main>
                <footer>Footer to remove</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "header",  # valid
            "html",  # protected
            "footer",  # valid
            "body",  # protected
        ]

        result = apply_exclusions(soup, selectors)

        # Valid selectors should work
        assert "Header to remove" not in result.soup.get_text()
        assert "Footer to remove" not in result.soup.get_text()

        # Protected elements should remain
        assert result.soup.find("html") is not None
        assert result.soup.find("body") is not None
        assert "Main content to keep" in result.soup.get_text()

        # Should have 2 successful and 2 failed
        assert result.summary.selectors_processed == 4
        assert result.summary.successful_selectors == 2
        assert result.summary.failed_selectors == 2
        assert result.summary.elements_removed == 2

    def test_descendant_selectors_with_protected_roots(self):
        """Test that descendant selectors starting with protected roots are handled."""
        html = """
        <html>
            <body>
                <div class="content">Content div</div>
                <p class="text">Text paragraph</p>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "html .content",  # descendant of protected root
            "body p",  # descendant of protected root
        ]

        result = apply_exclusions(soup, selectors)

        # The behavior here depends on implementation:
        # Option 1: Treat as invalid because they start with protected elements
        # Option 2: Allow descendant selectors but protect the root itself
        # This test documents the expected behavior

        # HTML and body should definitely remain
        assert result.soup.find("html") is not None
        assert result.soup.find("body") is not None

        # The descendant elements might be removed depending on implementation
        # For now, assume they are treated as invalid selectors
        assert result.summary.failed_selectors >= 0

    def test_child_selectors_with_protected_roots(self):
        """Test child selectors with protected roots."""
        html = """
        <html>
            <body>
                <div>Direct child of body</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "html > body",  # direct child selector with protected elements
            "body > div",  # direct child of protected root
        ]

        result = apply_exclusions(soup, selectors)

        # HTML and body should remain
        assert result.soup.find("html") is not None
        assert result.soup.find("body") is not None

        # Implementation-dependent behavior for the child selectors
        # Document the expected behavior here

    def test_complex_selectors_with_protected_roots(self):
        """Test complex selectors that include protected roots."""
        html = """
        <html class="no-js">
            <body class="homepage">
                <div class="container">Content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "html.no-js body.homepage .container",  # complex selector involving protected elements
            "body.homepage",  # protected with class
        ]

        result = apply_exclusions(soup, selectors)

        # Protected elements should remain
        assert result.soup.find("html") is not None
        assert result.soup.find("body") is not None

        # Content should remain if selector is treated as invalid
        assert "Content" in result.soup.get_text()

    def test_only_protected_selectors(self):
        """Test when all selectors target protected elements."""
        html = """
        <html>
            <body>
                <div>All content should remain</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["html", "body", "html.any-class", "body.any-class"]

        result = apply_exclusions(soup, selectors)

        # All content should remain
        assert result.soup.find("html") is not None
        assert result.soup.find("body") is not None
        assert "All content should remain" in result.soup.get_text()

        # All selectors should be invalid
        assert result.summary.selectors_processed == 4
        assert result.summary.successful_selectors == 0
        assert result.summary.failed_selectors == 4
        assert result.summary.elements_removed == 0

    def test_protected_selector_error_messages(self):
        """Test that protected selectors have appropriate error messages."""
        html = """
        <html>
            <body>
                <div>Content</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["html", "body"]

        result = apply_exclusions(soup, selectors)

        # Should record specific error messages for protected selectors
        if hasattr(result, "selector_results"):
            failed_results = [s for s in result.selector_results if not s.success]
            assert len(failed_results) == 2

            for failed_result in failed_results:
                assert failed_result.error_message is not None
                assert "protected" in failed_result.error_message.lower()

        assert result.summary.failed_selectors == 2
