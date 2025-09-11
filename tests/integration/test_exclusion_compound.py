"""Integration test for compound selectors removal."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import apply_exclusions


class TestCompoundSelectorRemoval:
    """Test exclusion functionality with compound CSS selectors."""

    def test_descendant_selector(self):
        """Test removing elements using descendant selectors."""
        html = """
        <html>
            <body>
                <div class="sidebar">
                    <div class="widget">Sidebar Widget</div>
                    <div class="advertisement">Sidebar Ad</div>
                </div>
                <main>
                    <div class="widget">Main Widget (keep)</div>
                    <div class="advertisement">Main Ad (keep)</div>
                    <article>Article content</article>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".sidebar .widget", ".sidebar .advertisement"]

        result = apply_exclusions(soup, selectors)

        # Sidebar widgets should be removed
        sidebar_widgets = result.soup.select(".sidebar .widget")
        sidebar_ads = result.soup.select(".sidebar .advertisement")
        assert len(sidebar_widgets) == 0
        assert len(sidebar_ads) == 0

        # Main widgets should remain
        assert result.soup.select("main .widget")
        assert result.soup.select("main .advertisement")
        assert "Main Widget (keep)" in result.soup.get_text()
        assert "Main Ad (keep)" in result.soup.get_text()
        assert "Sidebar Widget" not in result.soup.get_text()
        assert "Sidebar Ad" not in result.soup.get_text()

        # Check summary
        assert result.summary.elements_removed == 2

    def test_child_selector(self):
        """Test removing elements using direct child selectors."""
        html = """
        <html>
            <body>
                <div class="container">
                    <div class="item">Direct child (remove)</div>
                    <section>
                        <div class="item">Nested child (keep)</div>
                    </section>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".container > .item"]

        result = apply_exclusions(soup, selectors)

        # Direct child should be removed
        assert "Direct child (remove)" not in result.soup.get_text()

        # Nested child should remain
        assert "Nested child (keep)" in result.soup.get_text()

        # Check that exactly 1 element was removed
        assert result.summary.elements_removed == 1

    def test_attribute_selector(self):
        """Test removing elements using attribute selectors."""
        html = """
        <html>
            <body>
                <div data-role="advertisement">Ad 1</div>
                <div data-role="content">Content 1</div>
                <div data-role="advertisement">Ad 2</div>
                <div class="widget" data-role="sidebar">Sidebar</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ['[data-role="advertisement"]']

        result = apply_exclusions(soup, selectors)

        # Advertisement elements should be removed
        ad_elements = result.soup.find_all(attrs={"data-role": "advertisement"})
        assert len(ad_elements) == 0
        assert "Ad 1" not in result.soup.get_text()
        assert "Ad 2" not in result.soup.get_text()

        # Other elements should remain
        assert "Content 1" in result.soup.get_text()
        assert "Sidebar" in result.soup.get_text()

        # Check summary
        assert result.summary.elements_removed == 2

    def test_multiple_class_selector(self):
        """Test removing elements with multiple classes."""
        html = """
        <html>
            <body>
                <div class="widget sidebar">Sidebar Widget (remove)</div>
                <div class="widget main">Main Widget (keep)</div>
                <div class="sidebar">Sidebar (keep)</div>
                <div class="widget">Widget (keep)</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".widget.sidebar"]

        result = apply_exclusions(soup, selectors)

        # Only elements with both classes should be removed
        assert "Sidebar Widget (remove)" not in result.soup.get_text()

        # Elements with only one of the classes should remain
        assert "Main Widget (keep)" in result.soup.get_text()
        assert "Sidebar (keep)" in result.soup.get_text()
        assert "Widget (keep)" in result.soup.get_text()

        # Check summary
        assert result.summary.elements_removed == 1

    def test_pseudo_class_selector(self):
        """Test removing elements using pseudo-class selectors."""
        html = """
        <html>
            <body>
                <ul>
                    <li>First item</li>
                    <li>Second item</li>
                    <li>Third item</li>
                    <li>Fourth item</li>
                </ul>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["li:first-child", "li:last-child"]

        result = apply_exclusions(soup, selectors)

        # First and last items should be removed
        assert "First item" not in result.soup.get_text()
        assert "Fourth item" not in result.soup.get_text()

        # Middle items should remain
        assert "Second item" in result.soup.get_text()
        assert "Third item" in result.soup.get_text()

        # Check summary
        assert result.summary.elements_removed == 2

    def test_comma_separated_selector(self):
        """Test removing elements using comma-separated selectors."""
        html = """
        <html>
            <body>
                <header>Header content</header>
                <footer>Footer content</footer>
                <aside>Aside content</aside>
                <main>Main content</main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["header, footer, aside"]

        result = apply_exclusions(soup, selectors)

        # Header, footer, and aside should be removed
        assert "Header content" not in result.soup.get_text()
        assert "Footer content" not in result.soup.get_text()
        assert "Aside content" not in result.soup.get_text()

        # Main should remain
        assert "Main content" in result.soup.get_text()

        # Check summary - comma-separated counts as 1 selector
        assert result.summary.selectors_processed == 1
        assert result.summary.elements_removed == 3

    def test_complex_nested_compound_selector(self):
        """Test complex nested compound selectors."""
        html = """
        <html>
            <body>
                <div class="content">
                    <section class="article">
                        <div class="meta">
                            <span class="author">Author Name</span>
                            <span class="date">2024-01-01</span>
                        </div>
                        <p>Article text content here.</p>
                    </section>
                    <aside class="sidebar">
                        <div class="meta">
                            <span class="category">Category</span>
                        </div>
                    </aside>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".content .article .meta .date"]

        result = apply_exclusions(soup, selectors)

        # Only the specific nested element should be removed
        assert "2024-01-01" not in result.soup.get_text()

        # Other elements should remain
        assert "Author Name" in result.soup.get_text()
        assert "Article text content here." in result.soup.get_text()
        assert "Category" in result.soup.get_text()

        # Check summary
        assert result.summary.elements_removed == 1

    def test_invalid_compound_selector(self):
        """Test handling of invalid compound selectors."""
        html = """
        <html>
            <body>
                <div class="content">Content here</div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        # Invalid selector syntax
        selectors = [".content[unclosed .invalid"]

        result = apply_exclusions(soup, selectors)

        # Content should remain due to invalid selector
        assert "Content here" in result.soup.get_text()

        # Should be recorded as failed selector
        assert result.summary.failed_selectors >= 1
        assert result.summary.elements_removed == 0
