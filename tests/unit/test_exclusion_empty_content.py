"""Unit tests for empty primary content detection."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import (
    PRIMARY_CONTENT_SELECTORS,
    detect_empty_primary_content,
    is_content_element_empty,
)


class TestEmptyPrimaryContentDetection:
    """Test detection of empty primary content after exclusions."""

    def test_content_with_text_not_empty(self):
        """Test that elements with text content are not considered empty."""
        html = """
        <div>
            <article>
                <h1>Article Title</h1>
                <p>This is some content text.</p>
            </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is False

    def test_content_with_only_whitespace_is_empty(self):
        """Test that elements with only whitespace are considered empty."""
        html = """
        <div>
            <article>
                <p>   </p>
                <div>
                </div>
            </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is True

    def test_content_with_only_structural_elements_is_empty(self):
        """Test that elements with only structural elements are considered empty."""
        html = """
        <div>
            <article>
                <div></div>
                <span></span>
                <section></section>
            </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is True

    def test_content_with_images_not_empty(self):
        """Test that elements containing images are not considered empty."""
        html = """
        <div>
            <article>
                <img src="image.jpg" alt="Description">
            </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is False

    def test_content_with_links_not_empty(self):
        """Test that elements containing meaningful links are not considered empty."""
        html = """
        <div>
            <article>
                <a href="http://example.com">Read more</a>
            </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is False

    def test_completely_empty_element(self):
        """Test that completely empty elements are detected as empty."""
        html = """
        <div>
            <article></article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is True

    def test_detect_empty_primary_content_with_article(self):
        """Test detection when primary content element (article) is empty."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <article>   </article>
                <footer>Site Footer</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        empty_detected = detect_empty_primary_content(soup)
        assert empty_detected is True

    def test_detect_empty_primary_content_with_main(self):
        """Test detection when primary content element (main) is empty."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <main><div></div><span></span></main>
                <footer>Site Footer</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        empty_detected = detect_empty_primary_content(soup)
        assert empty_detected is True

    def test_detect_empty_primary_content_with_content(self):
        """Test no detection when primary content has actual content."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <article>
                    <h1>Article Title</h1>
                    <p>This is the article content.</p>
                </article>
                <footer>Site Footer</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        empty_detected = detect_empty_primary_content(soup)
        assert empty_detected is False

    def test_detect_empty_primary_content_no_primary_elements(self):
        """Test detection when no primary content elements exist."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <div>Some content</div>
                <footer>Site Footer</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        # This is a placeholder test - behavior may be clarified later
        empty_detected = detect_empty_primary_content(soup)
        # For now, assume no primary elements means empty primary content
        assert empty_detected is True

    def test_detect_empty_primary_content_multiple_elements(self):
        """Test detection with multiple primary content elements."""
        html = """
        <html>
            <body>
                <article></article>
                <main>
                    <h1>Main Content</h1>
                    <p>Actual content here.</p>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        # If any primary content element has content, should not be empty
        empty_detected = detect_empty_primary_content(soup)
        assert empty_detected is False

    def test_primary_content_selectors_defined(self):
        """Test that primary content selectors are properly defined."""
        # Ensure the selectors constant exists and has expected values
        assert PRIMARY_CONTENT_SELECTORS is not None
        assert "article" in PRIMARY_CONTENT_SELECTORS
        assert "main" in PRIMARY_CONTENT_SELECTORS
        assert '[role="main"]' in PRIMARY_CONTENT_SELECTORS

    def test_content_with_nested_text_not_empty(self):
        """Test that elements with nested text content are not considered empty."""
        html = """
        <div>
            <article>
                <div>
                    <section>
                        <p>Deeply nested content</p>
                    </section>
                </div>
            </article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")

        is_empty = is_content_element_empty(article)
        assert is_empty is False
