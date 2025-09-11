"""Integration test for empty primary content warning."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import apply_exclusions


class TestEmptyPrimaryContentWarning:
    """Test warning generation when primary content becomes empty after exclusions."""

    def test_article_becomes_empty_triggers_warning(self):
        """Test warning when article element becomes empty after exclusions."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <article>
                    <div class="advertisement">Large ad content</div>
                    <div class="social-share">Social sharing buttons</div>
                </article>
                <footer>Site Footer</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".advertisement", ".social-share"]

        result = apply_exclusions(soup, selectors)

        # Article should still exist but be empty
        article = result.soup.find("article")
        assert article is not None

        # Content should be removed
        assert "Large ad content" not in result.soup.get_text()
        assert "Social sharing buttons" not in result.soup.get_text()

        # Should detect empty primary content
        assert hasattr(result.summary, "empty_primary_content_warning")
        assert result.summary.empty_primary_content_warning is True

    def test_main_becomes_empty_triggers_warning(self):
        """Test warning when main element becomes empty after exclusions."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <main>
                    <div class="sidebar">Sidebar content</div>
                    <div class="widgets">Widget area</div>
                </main>
                <footer>Site Footer</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".sidebar", ".widgets"]

        result = apply_exclusions(soup, selectors)

        # Main should still exist but be empty
        main = result.soup.find("main")
        assert main is not None

        # Should detect empty primary content
        assert result.summary.empty_primary_content_warning is True

    def test_role_main_becomes_empty_triggers_warning(self):
        """Test warning when element with role='main' becomes empty."""
        html = """
        <html>
            <body>
                <div role="main">
                    <aside class="promotional">Promotional content</aside>
                    <div class="newsletter">Newsletter signup</div>
                </div>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".promotional", ".newsletter"]

        result = apply_exclusions(soup, selectors)

        # Role main element should exist but be empty
        main_role = result.soup.find(attrs={"role": "main"})
        assert main_role is not None

        # Should detect empty primary content
        assert result.summary.empty_primary_content_warning is True

    def test_primary_content_with_remaining_text_no_warning(self):
        """Test no warning when primary content still has meaningful text."""
        html = """
        <html>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>This is the main article content that should remain.</p>
                    <div class="advertisement">Remove this ad</div>
                    <p>More article content here.</p>
                </article>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".advertisement"]

        result = apply_exclusions(soup, selectors)

        # Article should have remaining content
        assert "Article Title" in result.soup.get_text()
        assert "main article content" in result.soup.get_text()
        assert "More article content" in result.soup.get_text()
        assert "Remove this ad" not in result.soup.get_text()

        # Should not detect empty primary content
        assert result.summary.empty_primary_content_warning is False

    def test_primary_content_with_only_whitespace_triggers_warning(self):
        """Test warning when primary content has only whitespace after exclusions."""
        html = """
        <html>
            <body>
                <article>
                    <div class="remove-all">
                        <p>All content to remove</p>
                        <span>More content to remove</span>
                    </div>
                </article>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".remove-all"]

        result = apply_exclusions(soup, selectors)

        # Article should exist but effectively empty
        article = result.soup.find("article")
        assert article is not None

        # Should detect empty primary content
        assert result.summary.empty_primary_content_warning is True

    def test_multiple_primary_elements_some_empty(self):
        """Test behavior when some primary elements are empty but others aren't."""
        html = """
        <html>
            <body>
                <article>
                    <div class="ads">Remove all ads</div>
                </article>
                <main>
                    <h1>Main Content Title</h1>
                    <p>This main content should remain.</p>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".ads"]

        result = apply_exclusions(soup, selectors)

        # Article should be empty, main should have content
        article = result.soup.find("article")
        main = result.soup.find("main")
        assert article is not None
        assert main is not None
        assert "Main Content Title" in result.soup.get_text()

        # Should NOT warn if at least one primary element has content
        assert result.summary.empty_primary_content_warning is False

    def test_no_primary_elements_triggers_warning(self):
        """Test warning when no primary content elements exist."""
        html = """
        <html>
            <body>
                <header>Header</header>
                <div class="content">
                    <p>Some content in div</p>
                </div>
                <footer>Footer</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".content"]  # Remove the only substantial content

        result = apply_exclusions(soup, selectors)

        # No article, main, or role="main" elements
        assert result.soup.find("article") is None
        assert result.soup.find("main") is None
        assert result.soup.find(attrs={"role": "main"}) is None

        # Should detect lack of primary content
        assert result.summary.empty_primary_content_warning is True

    def test_primary_content_with_images_no_warning(self):
        """Test no warning when primary content has images (even without text)."""
        html = """
        <html>
            <body>
                <article>
                    <img src="hero-image.jpg" alt="Article hero image">
                    <img src="diagram.jpg" alt="Technical diagram">
                    <div class="text-content">Remove this text</div>
                </article>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".text-content"]

        result = apply_exclusions(soup, selectors)

        # Article should still have images
        article = result.soup.find("article")
        assert article is not None
        images = article.find_all("img")
        assert len(images) == 2

        # Should not warn - images count as content
        assert result.summary.empty_primary_content_warning is False

    def test_primary_content_with_links_no_warning(self):
        """Test no warning when primary content has meaningful links."""
        html = """
        <html>
            <body>
                <main>
                    <a href="/related-article">Related Article</a>
                    <a href="/author-bio">About the Author</a>
                    <div class="ads">Advertisement content</div>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".ads"]

        result = apply_exclusions(soup, selectors)

        # Main should still have links
        main = result.soup.find("main")
        assert main is not None
        links = main.find_all("a")
        assert len(links) == 2

        # Should not warn - links count as content
        assert result.summary.empty_primary_content_warning is False

    def test_deeply_nested_primary_content_empty(self):
        """Test warning with deeply nested primary content structure."""
        html = """
        <html>
            <body>
                <main>
                    <div class="container">
                        <div class="wrapper">
                            <section class="content-section">
                                <div class="removable">All removable content</div>
                            </section>
                        </div>
                    </div>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".removable"]

        result = apply_exclusions(soup, selectors)

        # Main should exist but be effectively empty
        main = result.soup.find("main")
        assert main is not None

        # Should detect empty primary content
        assert result.summary.empty_primary_content_warning is True

    def test_mixed_empty_detection_scenarios(self):
        """Test complex scenario with multiple factors affecting empty detection."""
        html = """
        <html>
            <body>
                <article class="post">
                    <header class="post-header">
                        <h1>Post Title</h1>
                    </header>
                    <div class="post-content">
                        <div class="ads">Large advertisement</div>
                        <div class="social">Social media widgets</div>
                        <div class="newsletter">Newsletter signup</div>
                    </div>
                </article>
                <aside class="sidebar">Sidebar content</aside>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".ads", ".social", ".newsletter"]

        result = apply_exclusions(soup, selectors)

        # Article should still have the header with title
        assert "Post Title" in result.soup.get_text()

        # Should not warn because header content remains
        assert result.summary.empty_primary_content_warning is False
