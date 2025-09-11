"""Unit tests for selector resolver edge cases."""

import pytest
from bs4 import BeautifulSoup
from src.obsidian_capture.extract import (
    ExtractionError,
    ExtractionResult,
    NoSelectorMatchError,
    clean_text,
    extract_content_with_selectors,
    extract_element_by_selector,
    get_clean_text_content,
)


class TestCleanText:
    """Test text cleaning functionality."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text = "Hello    world\t\n  test"
        result = clean_text(text)
        assert result == "Hello world test"

    def test_remove_excessive_newlines(self):
        """Test removal of excessive newlines."""
        text = "Line 1\n\n\n\n\nLine 2\n\n\n\nLine 3"
        result = clean_text(text)
        assert result == "Line 1 Line 2 Line 3"

    def test_trim_whitespace(self):
        """Test trimming leading/trailing whitespace."""
        text = "   \n\n  Hello World  \n\n  "
        result = clean_text(text)
        assert result == "Hello World"

    def test_empty_text(self):
        """Test cleaning empty text."""
        result = clean_text("")
        assert result == ""

    def test_whitespace_only_text(self):
        """Test cleaning whitespace-only text."""
        result = clean_text("   \n\t  \n  ")
        assert result == ""


class TestExtractElementBySelector:
    """Test individual element extraction."""

    def test_valid_selector_match(self):
        """Test extracting element with valid selector."""
        html = "<div><p class='content'>Hello</p></div>"
        soup = BeautifulSoup(html, "html.parser")

        element = extract_element_by_selector(soup, "p.content")
        assert element is not None
        assert element.name == "p"
        assert element.get_text() == "Hello"

    def test_no_match(self):
        """Test no element matches selector."""
        html = "<div><p>Hello</p></div>"
        soup = BeautifulSoup(html, "html.parser")

        element = extract_element_by_selector(soup, ".nonexistent")
        assert element is None

    def test_invalid_selector(self):
        """Test invalid CSS selector."""
        html = "<div><p>Hello</p></div>"
        soup = BeautifulSoup(html, "html.parser")

        element = extract_element_by_selector(soup, "[[[invalid")
        assert element is None

    def test_multiple_matches_returns_first(self):
        """Test returns first element when multiple match."""
        html = "<div><p>First</p><p>Second</p></div>"
        soup = BeautifulSoup(html, "html.parser")

        element = extract_element_by_selector(soup, "p")
        assert element is not None
        assert element.get_text() == "First"


class TestGetCleanTextContent:
    """Test text content extraction."""

    def test_simple_text(self):
        """Test extracting simple text."""
        html = "<p>Hello world</p>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("p")

        text = get_clean_text_content(element)
        assert text == "Hello world"

    def test_nested_elements(self):
        """Test extracting text from nested elements."""
        html = "<div>Hello <span>nested</span> world</div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")

        text = get_clean_text_content(element)
        assert text == "Hello nested world"

    def test_whitespace_cleanup(self):
        """Test whitespace is properly cleaned."""
        html = "<p>  Hello\n\n\n   world  \t </p>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("p")

        text = get_clean_text_content(element)
        assert text == "Hello world"


class TestExtractContentWithSelectors:
    """Test content extraction with selector fallback."""

    def test_single_selector_success(self):
        """Test successful extraction with single selector."""
        html = """
        <div>
            <article class="content">
                This is a long enough piece of content that should match the minimum character requirement for extraction.
            </article>
        </div>
        """

        result = extract_content_with_selectors(html, ["article.content"], min_chars=50)

        assert isinstance(result, ExtractionResult)
        assert result.selector == "article.content"
        assert result.character_count >= 50
        assert "long enough piece of content" in result.text_content
        assert result.attempted_selectors == ["article.content"]

    def test_multiple_selectors_fallback(self):
        """Test fallback to second selector when first fails."""
        html = """
        <div>
            <section class="main">
                This is a very long piece of content in the main section that definitely meets the minimum character requirement.
            </section>
        </div>
        """

        result = extract_content_with_selectors(
            html, [".nonexistent", "section.main"], min_chars=50
        )

        assert result.selector == "section.main"
        assert result.character_count >= 50
        assert result.attempted_selectors == [".nonexistent", "section.main"]

    def test_no_selectors_provided(self):
        """Test error when no selectors provided."""
        html = "<div>Content</div>"

        with pytest.raises(ExtractionError, match="No selectors provided"):
            extract_content_with_selectors(html, [], min_chars=10)

    def test_invalid_html(self):
        """Test error handling for invalid HTML."""
        # BeautifulSoup is quite forgiving, so let's test with something that would cause parsing issues
        html = None

        with pytest.raises(ExtractionError, match="Failed to parse HTML"):
            extract_content_with_selectors(html, ["p"], min_chars=10)

    def test_no_selector_matches(self):
        """Test error when no selector matches any element."""
        html = "<div><p>Short</p></div>"

        with pytest.raises(NoSelectorMatchError, match="No selector matched content"):
            extract_content_with_selectors(
                html, [".nonexistent", "#missing"], min_chars=10
            )

    def test_content_too_short(self):
        """Test error when content is too short for min_chars."""
        html = "<div><p class='content'>Hi</p></div>"

        with pytest.raises(
            NoSelectorMatchError,
            match="No selector matched content with at least 50 characters",
        ):
            extract_content_with_selectors(html, ["p.content"], min_chars=50)

    def test_invalid_selector_continues_to_next(self):
        """Test invalid selector doesn't stop processing."""
        html = """
        <div>
            <p class="content">
                This is a long enough piece of content that should match the minimum character requirement.
            </p>
        </div>
        """

        result = extract_content_with_selectors(
            html, ["[[[invalid", "p.content"], min_chars=50
        )

        assert result.selector == "p.content"
        assert result.character_count >= 50

    def test_multiple_matching_elements_uses_first_valid(self):
        """Test uses first element that meets character requirement."""
        html = """
        <div>
            <p class="content">Short</p>
            <p class="content">
                This is a much longer piece of content that definitely meets the minimum character requirement for extraction.
            </p>
        </div>
        """

        result = extract_content_with_selectors(html, ["p.content"], min_chars=50)

        assert result.selector == "p.content"
        assert "much longer piece of content" in result.text_content
        assert result.character_count >= 50

    def test_html_fragment_preserved(self):
        """Test HTML fragment is preserved in result."""
        html = """
        <div>
            <article class="content">
                <h2>Title</h2>
                <p>This is a long enough piece of <strong>content</strong> that should match.</p>
            </article>
        </div>
        """

        result = extract_content_with_selectors(html, ["article.content"], min_chars=30)

        assert "<h2>Title</h2>" in result.html_fragment
        assert "<strong>content</strong>" in result.html_fragment
        assert result.html_fragment.startswith('<article class="content">')

    def test_zero_min_chars(self):
        """Test extraction with zero minimum characters."""
        html = "<div><p class='content'>Hi</p></div>"

        result = extract_content_with_selectors(html, ["p.content"], min_chars=0)

        assert result.text_content == "Hi"
        assert result.character_count == 2

    def test_complex_nested_content(self):
        """Test extraction from complex nested structure."""
        html = """
        <div class="wrapper">
            <article class="post">
                <header>
                    <h1>Article Title</h1>
                    <div class="meta">Author: John Doe</div>
                </header>
                <div class="content">
                    <p>This is the first paragraph of a very long article with multiple paragraphs.</p>
                    <p>This is the second paragraph with more <em>emphasized</em> content.</p>
                    <blockquote>A quote within the article.</blockquote>
                    <p>Final paragraph to ensure we have enough content.</p>
                </div>
            </article>
        </div>
        """

        result = extract_content_with_selectors(html, ["article.post"], min_chars=100)

        assert "Article Title" in result.text_content
        assert "first paragraph" in result.text_content
        assert "emphasized" in result.text_content
        assert "A quote within" in result.text_content
        assert result.character_count >= 100
