"""Integration test for nested selector behavior (parent + child)."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import apply_exclusions


class TestNestedSelectorBehavior:
    """Test exclusion behavior with nested selectors and parent-child relationships."""

    def test_remove_parent_removes_children(self):
        """Test that removing a parent element also removes its children."""
        html = """
        <html>
            <body>
                <div class="sidebar">
                    <div class="widget">Widget 1</div>
                    <div class="advertisement">Ad 1</div>
                    <ul class="menu">
                        <li>Menu Item 1</li>
                        <li>Menu Item 2</li>
                    </ul>
                </div>
                <main>Main content</main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".sidebar"]

        result = apply_exclusions(soup, selectors)

        # Parent and all children should be gone
        assert result.soup.find(class_="sidebar") is None
        assert "Widget 1" not in result.soup.get_text()
        assert "Ad 1" not in result.soup.get_text()
        assert "Menu Item 1" not in result.soup.get_text()
        assert "Menu Item 2" not in result.soup.get_text()

        # Main content should remain
        assert "Main content" in result.soup.get_text()

        # Should count as removing the parent element (children are implicitly removed)
        assert result.summary.elements_removed == 1

    def test_remove_child_leaves_parent(self):
        """Test that removing a child element leaves the parent intact."""
        html = """
        <html>
            <body>
                <div class="container">
                    <h2>Container Title</h2>
                    <div class="advertisement">Remove this ad</div>
                    <p>Container content</p>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".advertisement"]

        result = apply_exclusions(soup, selectors)

        # Child should be removed
        assert "Remove this ad" not in result.soup.get_text()

        # Parent and siblings should remain
        container = result.soup.find(class_="container")
        assert container is not None
        assert "Container Title" in result.soup.get_text()
        assert "Container content" in result.soup.get_text()

        # Only the child element should be counted
        assert result.summary.elements_removed == 1

    def test_overlapping_parent_child_selectors_parent_first(self):
        """Test behavior when both parent and child are targeted (parent selector first)."""
        html = """
        <html>
            <body>
                <div class="sidebar">
                    <div class="widget">Widget content</div>
                    <p>Other sidebar content</p>
                </div>
                <main>Main content</main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        # Parent selector first, then child
        selectors = [".sidebar", ".widget"]

        result = apply_exclusions(soup, selectors)

        # Parent should be removed (and child with it)
        assert result.soup.find(class_="sidebar") is None
        assert "Widget content" not in result.soup.get_text()
        assert "Other sidebar content" not in result.soup.get_text()

        # Main content should remain
        assert "Main content" in result.soup.get_text()

        # First selector removes parent, second selector finds nothing to remove
        # Implementation may vary: could be 1 removal + 1 no-op, or 2 removals
        assert result.summary.elements_removed >= 1

    def test_overlapping_parent_child_selectors_child_first(self):
        """Test behavior when both parent and child are targeted (child selector first)."""
        html = """
        <html>
            <body>
                <div class="sidebar">
                    <div class="widget">Widget content</div>
                    <p>Other sidebar content</p>
                </div>
                <main>Main content</main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        # Child selector first, then parent
        selectors = [".widget", ".sidebar"]

        result = apply_exclusions(soup, selectors)

        # Both elements should be gone
        assert result.soup.find(class_="sidebar") is None
        assert result.soup.find(class_="widget") is None
        assert "Widget content" not in result.soup.get_text()
        assert "Other sidebar content" not in result.soup.get_text()

        # Main content should remain
        assert "Main content" in result.soup.get_text()

        # Implementation dependent: child removed first, then parent (or parent removes already-gone child)
        assert result.summary.elements_removed >= 1

    def test_deeply_nested_removal(self):
        """Test removing elements from deeply nested structures."""
        html = """
        <html>
            <body>
                <div class="level1">
                    <div class="level2">
                        <div class="level3">
                            <div class="level4">
                                <span class="target">Deep target</span>
                                <span class="keep">Keep this</span>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".target"]

        result = apply_exclusions(soup, selectors)

        # Target should be removed
        assert "Deep target" not in result.soup.get_text()

        # All parent levels and sibling should remain
        assert result.soup.find(class_="level1") is not None
        assert result.soup.find(class_="level2") is not None
        assert result.soup.find(class_="level3") is not None
        assert result.soup.find(class_="level4") is not None
        assert "Keep this" in result.soup.get_text()

        assert result.summary.elements_removed == 1

    def test_multiple_children_selective_removal(self):
        """Test selectively removing some children while keeping others."""
        html = """
        <html>
            <body>
                <article class="post">
                    <header class="post-header">Post Title</header>
                    <div class="post-content">
                        <p>First paragraph</p>
                        <div class="advertisement">Ad content</div>
                        <p>Second paragraph</p>
                        <div class="social-share">Share buttons</div>
                        <p>Third paragraph</p>
                    </div>
                    <footer class="post-footer">Post footer</footer>
                </article>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".advertisement", ".social-share"]

        result = apply_exclusions(soup, selectors)

        # Targeted children should be removed
        assert "Ad content" not in result.soup.get_text()
        assert "Share buttons" not in result.soup.get_text()

        # Parent and other children should remain
        assert result.soup.find(class_="post") is not None
        assert "Post Title" in result.soup.get_text()
        assert "First paragraph" in result.soup.get_text()
        assert "Second paragraph" in result.soup.get_text()
        assert "Third paragraph" in result.soup.get_text()
        assert "Post footer" in result.soup.get_text()

        assert result.summary.elements_removed == 2

    def test_nested_selectors_with_same_class(self):
        """Test handling nested elements with the same class name."""
        html = """
        <html>
            <body>
                <div class="container">
                    <div class="item">Outer item</div>
                    <section>
                        <div class="item">
                            <div class="item">Nested item</div>
                        </div>
                    </section>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".item"]

        result = apply_exclusions(soup, selectors)

        # All elements with the class should be removed
        items = result.soup.find_all(class_="item")
        assert len(items) == 0
        assert "Outer item" not in result.soup.get_text()
        assert "Nested item" not in result.soup.get_text()

        # Container should remain
        assert result.soup.find(class_="container") is not None

        # All matching elements should be counted
        # Note: when parent .item is removed, child .item goes with it
        # The count depends on DOM processing order
        assert result.summary.elements_removed >= 2

    def test_empty_parent_after_child_removal(self):
        """Test parent remains even if empty after child removal."""
        html = """
        <html>
            <body>
                <div class="container">
                    <div class="only-child">Only content</div>
                </div>
                <p>Other content</p>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".only-child"]

        result = apply_exclusions(soup, selectors)

        # Child should be removed
        assert "Only content" not in result.soup.get_text()

        # Parent should remain (even if now empty)
        container = result.soup.find(class_="container")
        assert container is not None

        # Other content should remain
        assert "Other content" in result.soup.get_text()

        assert result.summary.elements_removed == 1
