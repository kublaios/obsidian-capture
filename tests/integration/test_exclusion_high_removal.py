"""Integration test for high removal ratio triggers warning."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import apply_exclusions


class TestHighRemovalRatioWarning:
    """Test warning generation when high percentage of elements are removed."""

    def test_low_removal_ratio_no_warning(self):
        """Test that low removal ratios don't trigger warnings."""
        # Create HTML with many elements, remove only a few
        html = """
        <html>
            <body>
                <div class="container">
                    <article>
                        <h1>Title</h1>
                        <p>Paragraph 1</p>
                        <p>Paragraph 2</p>
                        <p>Paragraph 3</p>
                        <p>Paragraph 4</p>
                        <p>Paragraph 5</p>
                        <section class="content">
                            <div>Content div 1</div>
                            <div>Content div 2</div>
                            <div>Content div 3</div>
                        </section>
                    </article>
                    <footer>Footer to remove</footer>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["footer"]  # Remove only 1 element out of many

        result = apply_exclusions(soup, selectors)

        # Should have removed elements
        assert result.summary.elements_removed > 0
        assert "Footer to remove" not in result.soup.get_text()

        # Removal ratio should be low (well below 40%)
        assert result.summary.removal_ratio < 0.4
        assert result.summary.high_removal_warning is False

    def test_high_removal_ratio_triggers_warning(self):
        """Test that high removal ratios (>=40%) trigger warnings."""
        # Create HTML where we'll remove a large portion
        html = """
        <html>
            <body>
                <div class="content">Keep this</div>
                <div class="remove-me">Remove 1</div>
                <div class="remove-me">Remove 2</div>
                <div class="remove-me">Remove 3</div>
                <div class="remove-me">Remove 4</div>
                <div class="remove-me">Remove 5</div>
                <div class="remove-me">Remove 6</div>
                <div class="remove-me">Remove 7</div>
                <div class="remove-me">Remove 8</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".remove-me"]  # Remove 8 out of ~12 elements (>60%)

        result = apply_exclusions(soup, selectors)

        # Should have removed many elements
        assert result.summary.elements_removed == 8
        assert "Keep this" in result.soup.get_text()
        assert "Remove 1" not in result.soup.get_text()

        # Should trigger high removal warning
        assert result.summary.removal_ratio >= 0.4
        assert result.summary.high_removal_warning is True

    def test_exactly_at_threshold_triggers_warning(self):
        """Test that exactly 40% removal triggers warning."""
        # Create HTML and remove exactly 40% of elements to trigger threshold
        html = """
        <html>
            <body>
                <div>Keep 1</div>
                <div>Keep 2</div>
                <div>Keep 3</div>
                <div class="remove">Remove 1</div>
                <div class="remove">Remove 2</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        # Total elements: html, body, 5 divs = 7 elements
        # Removing 2 elements: 2/7 = 0.286 (still below threshold)
        # Let's remove 3 elements: 3/7 = 0.429 (above threshold)
        selectors = [".remove", "div:first-child"]  # This will remove 3 total

        result = apply_exclusions(soup, selectors)

        # Should remove exactly 3 elements (2 with class "remove" + 1 first div)
        assert result.summary.elements_removed == 3

        # 3/7 = 0.428... which is above 40% threshold
        assert result.summary.removal_ratio > 0.4
        assert result.summary.high_removal_warning is True

    def test_very_high_removal_ratio_warning(self):
        """Test warning with very high removal ratios (>80%)."""
        html = """
        <html>
            <body>
                <div class="keep">Keep this one</div>
                <div class="advertisement">Ad 1</div>
                <div class="advertisement">Ad 2</div>
                <div class="advertisement">Ad 3</div>
                <div class="advertisement">Ad 4</div>
                <div class="advertisement">Ad 5</div>
                <div class="advertisement">Ad 6</div>
                <div class="advertisement">Ad 7</div>
                <div class="advertisement">Ad 8</div>
                <div class="advertisement">Ad 9</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        # Total elements: html, body, 10 divs = 12 elements
        # Removing 9 elements: 9/12 = 0.75 = 75%
        selectors = [".advertisement"]  # Remove 9 out of 12 total = 75%

        result = apply_exclusions(soup, selectors)

        # Should remove most elements
        assert result.summary.elements_removed == 9
        assert "Keep this one" in result.soup.get_text()

        # Should have high removal ratio (75% > 40%)
        assert (
            result.summary.removal_ratio >= 0.7
        )  # 75% is high enough to trigger warning
        assert result.summary.high_removal_warning is True

    def test_multiple_selectors_combined_high_removal(self):
        """Test warning when multiple selectors combine to high removal."""
        html = """
        <html>
            <body>
                <article>Keep article</article>
                <footer>Remove footer</footer>
                <aside>Remove aside</aside>
                <nav>Remove nav</nav>
                <div class="ads">Remove ads</div>
                <div class="sidebar">Remove sidebar</div>
                <div class="widgets">Remove widgets</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["footer", "aside", "nav", ".ads", ".sidebar"]  # Remove 5 out of 7

        result = apply_exclusions(soup, selectors)

        # Should remove multiple elements
        assert result.summary.elements_removed == 5
        assert "Keep article" in result.soup.get_text()
        assert "Remove footer" not in result.soup.get_text()

        # Combined removal should be high
        removal_ratio = 5 / result.summary.original_element_count
        assert removal_ratio >= 0.4  # Depends on total element count
        assert result.summary.high_removal_warning is True

    def test_no_elements_removed_no_warning(self):
        """Test that removing no elements doesn't trigger warning."""
        html = """
        <html>
            <body>
                <div>Content 1</div>
                <div>Content 2</div>
                <div>Content 3</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".nonexistent"]  # No matches

        result = apply_exclusions(soup, selectors)

        # Should remove nothing
        assert result.summary.elements_removed == 0
        assert result.summary.removal_ratio == 0.0
        assert result.summary.high_removal_warning is False

    def test_complete_removal_triggers_warning(self):
        """Test that removing all removable elements triggers warning."""
        html = """
        <html>
            <body>
                <div class="content">Content 1</div>
                <div class="content">Content 2</div>
                <div class="content">Content 3</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".content"]  # Remove all content divs

        result = apply_exclusions(soup, selectors)

        # Should remove all matching elements
        assert result.summary.elements_removed == 3
        assert "Content 1" not in result.soup.get_text()

        # Should trigger warning for high removal
        assert result.summary.high_removal_warning is True

    def test_mixed_success_failure_high_removal_warning(self):
        """Test warning calculation with mixed successful/failed selectors."""
        html = """
        <html>
            <body>
                <div class="keep">Keep</div>
                <footer>Remove footer</footer>
                <aside>Remove aside</aside>
                <nav>Remove nav</nav>
                <div class="ads">Remove ads</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [
            "footer",  # valid
            "div[invalid",  # invalid selector
            "aside",  # valid
            "html",  # invalid (protected)
            "nav",  # valid
            ".ads",  # valid
        ]

        result = apply_exclusions(soup, selectors)

        # Should have mixed success/failure
        assert result.summary.successful_selectors > 0
        assert result.summary.failed_selectors > 0

        # Warning should be based on actual removals vs original count
        if (
            result.summary.elements_removed
            >= 0.4 * result.summary.original_element_count
        ):
            assert result.summary.high_removal_warning is True

    def test_large_document_high_removal_warning(self):
        """Test warning with larger document structure."""
        # Create a larger HTML structure
        html = """
        <html>
            <body>
                <header>
                    <h1>Site Title</h1>
                    <nav>Navigation</nav>
                </header>
                <main>
                    <article>
                        <h2>Article Title</h2>
                        <p>Paragraph 1</p>
                        <p>Paragraph 2</p>
                    </article>
                </main>
                <aside class="sidebar">
                    <div class="widget">Widget 1</div>
                    <div class="widget">Widget 2</div>
                    <div class="widget">Widget 3</div>
                    <div class="widget">Widget 4</div>
                    <div class="widget">Widget 5</div>
                    <div class="widget">Widget 6</div>
                </aside>
                <footer>
                    <p>Footer content</p>
                </footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        # Remove sidebar (with all widgets) + footer + nav
        selectors = [".sidebar", "footer", "nav"]

        result = apply_exclusions(soup, selectors)

        # Should remove significant portion
        assert result.summary.elements_removed > 0
        assert "Widget 1" not in result.soup.get_text()
        assert "Footer content" not in result.soup.get_text()
        assert "Navigation" not in result.soup.get_text()

        # Keep main content
        assert "Article Title" in result.soup.get_text()
        assert "Paragraph 1" in result.soup.get_text()

        # Should potentially trigger warning if removal ratio is high enough
        if result.summary.removal_ratio >= 0.4:
            assert result.summary.high_removal_warning is True
