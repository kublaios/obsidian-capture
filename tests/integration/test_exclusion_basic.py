"""Integration test for basic removal (footer + subscribe offer)."""

from bs4 import BeautifulSoup
from src.obsidian_capture.exclude import (
    apply_exclusions,
)


class TestBasicExclusionRemoval:
    """Test basic exclusion functionality with common selectors."""

    def test_remove_footer_element(self):
        """Test removing footer element from HTML."""
        html = """
        <html>
            <body>
                <header>Site Header</header>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <p>Article content goes here.</p>
                    </article>
                </main>
                <footer>Site Footer with links</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["footer"]

        result = apply_exclusions(soup, selectors)

        # Footer should be removed
        remaining_footers = result.soup.find_all("footer")
        assert len(remaining_footers) == 0

        # Other elements should remain
        assert result.soup.find("header") is not None
        assert result.soup.find("main") is not None
        assert result.soup.find("article") is not None

        # Check summary
        assert result.summary.selectors_processed == 1
        assert result.summary.successful_selectors == 1
        assert result.summary.failed_selectors == 0
        assert result.summary.elements_removed == 1

    def test_remove_subscribe_offer_by_class(self):
        """Test removing subscribe offer by CSS class."""
        html = """
        <html>
            <body>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <p>Article content goes here.</p>
                        <div class="subscribe-offer">
                            <h3>Subscribe Now!</h3>
                            <p>Get our newsletter</p>
                            <button>Subscribe</button>
                        </div>
                        <p>More article content.</p>
                    </article>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".subscribe-offer"]

        result = apply_exclusions(soup, selectors)

        # Subscribe offer should be removed
        subscribe_elements = result.soup.find_all(class_="subscribe-offer")
        assert len(subscribe_elements) == 0

        # Article content should remain
        article = result.soup.find("article")
        assert article is not None
        assert "Article content goes here." in article.get_text()
        assert "More article content." in article.get_text()
        assert "Subscribe Now!" not in article.get_text()

        # Check summary
        assert result.summary.selectors_processed == 1
        assert result.summary.successful_selectors == 1
        assert result.summary.elements_removed == 1

    def test_remove_both_footer_and_subscribe_offer(self):
        """Test removing both footer and subscribe offer."""
        html = """
        <html>
            <body>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <p>Article content goes here.</p>
                        <div class="subscribe-offer">
                            <h3>Subscribe Now!</h3>
                        </div>
                    </article>
                </main>
                <footer>
                    <p>Site Footer</p>
                </footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = ["footer", ".subscribe-offer"]

        result = apply_exclusions(soup, selectors)

        # Both elements should be removed
        assert len(result.soup.find_all("footer")) == 0
        assert len(result.soup.find_all(class_="subscribe-offer")) == 0

        # Article content should remain
        article = result.soup.find("article")
        assert article is not None
        assert "Article content goes here." in article.get_text()
        assert "Subscribe Now!" not in article.get_text()
        assert "Site Footer" not in result.soup.get_text()

        # Check summary
        assert result.summary.selectors_processed == 2
        assert result.summary.successful_selectors == 2
        assert result.summary.failed_selectors == 0
        assert result.summary.elements_removed == 2

    def test_remove_multiple_elements_same_selector(self):
        """Test removing multiple elements matching the same selector."""
        html = """
        <html>
            <body>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <p>Content paragraph 1</p>
                        <div class="ad-banner">Ad 1</div>
                        <p>Content paragraph 2</p>
                        <div class="ad-banner">Ad 2</div>
                        <p>Content paragraph 3</p>
                        <div class="ad-banner">Ad 3</div>
                    </article>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".ad-banner"]

        result = apply_exclusions(soup, selectors)

        # All ad banners should be removed
        ad_elements = result.soup.find_all(class_="ad-banner")
        assert len(ad_elements) == 0

        # Content paragraphs should remain
        paragraphs = result.soup.find_all("p")
        assert len(paragraphs) == 3
        assert "Content paragraph 1" in result.soup.get_text()
        assert "Content paragraph 2" in result.soup.get_text()
        assert "Content paragraph 3" in result.soup.get_text()
        assert "Ad 1" not in result.soup.get_text()

        # Check summary - 3 elements removed with 1 selector
        assert result.summary.selectors_processed == 1
        assert result.summary.successful_selectors == 1
        assert result.summary.failed_selectors == 0
        assert result.summary.elements_removed == 3

    def test_no_elements_match_selector(self):
        """Test behavior when no elements match the selector."""
        html = """
        <html>
            <body>
                <main>
                    <article>
                        <h1>Article Title</h1>
                        <p>Article content goes here.</p>
                    </article>
                </main>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        selectors = [".non-existent-class"]

        result = apply_exclusions(soup, selectors)

        # No elements should be removed
        assert result.summary.elements_removed == 0

        # All original content should remain
        assert result.soup.find("article") is not None
        assert "Article content goes here." in result.soup.get_text()

        # Selector should still be counted as processed (and successful if no error)
        assert result.summary.selectors_processed == 1
        # This might be successful (found 0 elements) or failed depending on implementation
        assert (
            result.summary.successful_selectors + result.summary.failed_selectors == 1
        )

    def test_original_element_count_tracking(self):
        """Test that original element count is properly tracked."""
        html = """
        <html>
            <body>
                <div>1</div>
                <div>2</div>
                <p>3</p>
                <span>4</span>
                <footer>5</footer>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        original_count = len(soup.find_all())
        selectors = ["footer"]

        result = apply_exclusions(soup, selectors)

        # Original count should be tracked
        assert result.summary.original_element_count == original_count
        assert result.summary.elements_removed == 1

        # Removal ratio should be calculated correctly
        expected_ratio = 1 / original_count
        assert abs(result.summary.removal_ratio - expected_ratio) < 0.001
