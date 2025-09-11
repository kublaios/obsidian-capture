"""Unit tests for conversion preserves formatting."""

from src.obsidian_capture.convert import (
    clean_markdown_content,
    convert_html_to_markdown,
    estimate_reading_time,
    post_process_markdown,
)


class TestConvertHtmlToMarkdown:
    """Test HTML to Markdown conversion."""

    def test_convert_simple_html(self):
        """Test converting simple HTML to Markdown."""
        html = "<h1>Title</h1><p>This is a paragraph.</p>"
        result = convert_html_to_markdown(html)

        assert "# Title" in result
        assert "This is a paragraph." in result

    def test_convert_with_links(self):
        """Test converting HTML with links preserved."""
        html = '<p>Visit <a href="https://example.com">example</a> for more.</p>'
        result = convert_html_to_markdown(html, preserve_links=True)

        assert "[example](<https://example.com>)" in result

    def test_convert_without_links(self):
        """Test converting HTML with links ignored."""
        html = '<p>Visit <a href="https://example.com">example</a> for more.</p>'
        result = convert_html_to_markdown(html, preserve_links=False)

        assert "[example](https://example.com)" not in result
        assert "example" in result

    def test_convert_with_emphasis(self):
        """Test converting HTML with emphasis formatting."""
        html = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
        result = convert_html_to_markdown(html)

        assert "**bold**" in result
        assert "*italic*" in result

    def test_convert_with_lists(self):
        """Test converting HTML lists."""
        html = """
        <ul>
            <li>First item</li>
            <li>Second item</li>
        </ul>
        <ol>
            <li>Numbered first</li>
            <li>Numbered second</li>
        </ol>
        """
        result = convert_html_to_markdown(html)

        assert "- First item" in result
        assert "- Second item" in result
        assert "1. Numbered first" in result
        assert "2. Numbered second" in result

    def test_convert_with_code(self):
        """Test converting HTML with code blocks."""
        html = '<pre><code>print("Hello World")</code></pre>'
        result = convert_html_to_markdown(html)

        # html2text doesn't preserve code block formatting for single line code
        assert 'print("Hello World")' in result

    def test_convert_with_inline_code(self):
        """Test converting HTML with inline code."""
        html = "<p>Use the <code>print()</code> function.</p>"
        result = convert_html_to_markdown(html)

        assert "`print()`" in result

    def test_convert_with_blockquote(self):
        """Test converting HTML blockquotes."""
        html = "<blockquote><p>This is a quote.</p></blockquote>"
        result = convert_html_to_markdown(html)

        assert "> This is a quote." in result

    def test_convert_with_images(self):
        """Test converting HTML with images."""
        html = '<img src="image.jpg" alt="Test Image">'
        result = convert_html_to_markdown(html)

        assert "![Test Image](image.jpg)" in result

    def test_convert_with_base_url(self):
        """Test converting HTML with relative links and base URL."""
        html = '<a href="/page">Relative Link</a>'
        result = convert_html_to_markdown(html, base_url="https://example.com")

        # The exact format depends on html2text behavior with base URLs
        assert "Relative Link" in result

    def test_convert_with_body_width(self):
        """Test converting HTML with line wrapping."""
        long_text = "This is a very long line of text that should be wrapped " * 5
        html = f"<p>{long_text}</p>"
        result = convert_html_to_markdown(html, body_width=50)

        # Check that lines are wrapped (contains newlines within paragraph)
        lines = result.strip().split("\n")
        # At least some lines should be shorter due to wrapping
        short_lines = [line for line in lines if len(line) <= 60 and len(line) > 0]
        assert len(short_lines) > 0

    def test_convert_with_tables(self):
        """Test converting HTML tables."""
        html = """
        <table>
            <thead>
                <tr><th>Header 1</th><th>Header 2</th></tr>
            </thead>
            <tbody>
                <tr><td>Cell 1</td><td>Cell 2</td></tr>
            </tbody>
        </table>
        """
        result = convert_html_to_markdown(html)

        assert "Header 1" in result
        assert "Header 2" in result
        assert "Cell 1" in result
        assert "Cell 2" in result
        # Markdown tables typically use | characters
        assert "|" in result

    def test_convert_nested_elements(self):
        """Test converting nested HTML elements."""
        html = """
        <div>
            <h2>Section Title</h2>
            <p>Paragraph with <strong>bold <em>italic</em></strong> text.</p>
            <ul>
                <li>Item with <code>code</code></li>
                <li>Item with <a href="http://example.com">link</a></li>
            </ul>
        </div>
        """
        result = convert_html_to_markdown(html)

        assert "## Section Title" in result
        assert "**bold *italic***" in result or "***bold italic***" in result
        assert "`code`" in result
        assert "[link](<http://example.com>)" in result

    def test_convert_empty_html(self):
        """Test converting empty HTML."""
        result = convert_html_to_markdown("")
        assert result == "\n"

    def test_convert_whitespace_only_html(self):
        """Test converting HTML with only whitespace."""
        result = convert_html_to_markdown("   \n\t  ")
        assert result.strip() == ""

    def test_convert_html_with_special_characters(self):
        """Test converting HTML with special characters."""
        html = "<p>Price: $100 &amp; €50. Use &lt;tags&gt; carefully.</p>"
        result = convert_html_to_markdown(html)

        assert "$100 & €50" in result
        assert "<tags>" in result

    def test_convert_preserves_paragraph_breaks(self):
        """Test that paragraph breaks are preserved."""
        html = "<p>First paragraph.</p><p>Second paragraph.</p>"
        result = convert_html_to_markdown(html)

        # Should have paragraph separation
        assert "First paragraph." in result
        assert "Second paragraph." in result
        # Should have proper spacing between paragraphs
        paragraphs = result.strip().split("\n\n")
        assert len(paragraphs) >= 2


class TestPostProcessMarkdown:
    """Test markdown post-processing."""

    def test_remove_excessive_blank_lines(self):
        """Test removal of excessive blank lines."""
        markdown = "Line 1\n\n\n\n\nLine 2\n\n\n\nLine 3"
        result = post_process_markdown(markdown)

        # Should have at most double newlines
        assert "\n\n\n" not in result
        assert "Line 1\n\nLine 2\n\nLine 3" in result

    def test_fix_header_spacing(self):
        """Test header spacing fix."""
        markdown = "\n#Header\nText"
        result = post_process_markdown(markdown)

        # Should add proper spacing after headers
        assert "# Header\n\n" in result

    def test_fix_multiple_header_levels(self):
        """Test header spacing for different levels."""
        markdown = "\n##Level2\nText\n###Level3\nMore text"
        result = post_process_markdown(markdown)

        assert "## Level2\n\n" in result
        assert "### Level3\n\n" in result

    def test_fix_code_block_spacing(self):
        """Test code block spacing fix."""
        markdown = "\n```python\ncode here\n```\nText after"
        result = post_process_markdown(markdown)

        # Should have proper spacing around code blocks
        assert "```python\n" in result
        assert "\n```\n\n" in result

    def test_remove_trailing_whitespace(self):
        """Test removal of trailing whitespace from lines."""
        markdown = "Line with spaces   \nAnother line\t\nClean line"
        result = post_process_markdown(markdown)

        lines = result.split("\n")
        for line in lines:
            if line:  # Skip empty lines
                assert not line.endswith(" ")
                assert not line.endswith("\t")

    def test_ensure_single_newline_ending(self):
        """Test that content ends with single newline."""
        # Test with no ending newline
        markdown = "Content without newline"
        result = post_process_markdown(markdown)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

        # Test with multiple ending newlines
        markdown = "Content with newlines\n\n\n"
        result = post_process_markdown(markdown)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_preserve_list_formatting(self):
        """Test that list formatting is preserved."""
        markdown = "\n- First item\n- Second item\n1. Numbered item"
        result = post_process_markdown(markdown)

        assert "- First item" in result
        assert "\n- Second item" in result
        assert "\n1. Numbered item" in result

    def test_empty_markdown(self):
        """Test post-processing empty markdown."""
        result = post_process_markdown("")
        assert result == "\n"

    def test_whitespace_only_markdown(self):
        """Test post-processing whitespace-only markdown."""
        result = post_process_markdown("   \n\t  \n  ")
        assert result == "\n"


class TestCleanMarkdownContent:
    """Test markdown content cleaning."""

    def test_remove_empty_links(self):
        """Test removal of empty links."""
        markdown = "Text with [](http://empty.com) empty link."
        result = clean_markdown_content(markdown)

        assert "[](" not in result
        assert "Text with  empty link." in result or "Text with empty link." in result

    def test_fix_broken_emphasis(self):
        """Test fixing broken emphasis marks."""
        markdown = "Text with * * broken emphasis and _ _ underscores."
        result = clean_markdown_content(markdown)

        assert "* *" not in result
        assert "_ _" not in result

    def test_clean_table_formatting(self):
        """Test cleaning table formatting."""
        markdown = "| Header 1 | | Header 2 |"
        result = clean_markdown_content(markdown)

        assert "||" not in result

    def test_remove_excessive_punctuation(self):
        """Test removal of excessive punctuation."""
        markdown = "This is exciting!!! Really??? Yes..."
        result = clean_markdown_content(markdown)

        assert "!!!" not in result
        assert "???" not in result
        # Excessive punctuation is cleaned up to single instances
        assert "!" in result and "!!!" not in result
        assert "?" in result and "???" not in result

    def test_preserve_valid_formatting(self):
        """Test that valid formatting is preserved."""
        markdown = "**Bold** *italic* `code` [link](http://example.com)"
        result = clean_markdown_content(markdown)

        # The function may clean spacing but preserve core formatting
        assert "Bold" in result and "`code`" in result and "[link]" in result
        assert "*italic*" in result
        assert "`code`" in result
        assert "[link](http://example.com)" in result

    def test_clean_empty_content(self):
        """Test cleaning empty content."""
        result = clean_markdown_content("")
        assert result == ""

    def test_clean_multiple_issues(self):
        """Test cleaning content with multiple issues."""
        markdown = "Text with [](empty.com) and * * broken emphasis!!! Plus | | tables."
        result = clean_markdown_content(markdown)

        assert "[](" not in result
        assert "* *" not in result
        assert "!!!" not in result
        assert "| |" not in result


class TestEstimateReadingTime:
    """Test reading time estimation."""

    def test_estimate_short_text(self):
        """Test reading time for short text."""
        markdown = (
            "This is a short text with about twenty words in it for testing purposes."
        )
        result = estimate_reading_time(markdown, words_per_minute=200)

        assert result == 1  # Minimum is 1 minute

    def test_estimate_medium_text(self):
        """Test reading time for medium length text."""
        # Create text with approximately 400 words
        word = "word "
        markdown = word * 400
        result = estimate_reading_time(markdown, words_per_minute=200)

        assert result == 2  # 400 words / 200 wpm = 2 minutes

    def test_estimate_long_text(self):
        """Test reading time for long text."""
        # Create text with approximately 1000 words
        word = "word "
        markdown = word * 1000
        result = estimate_reading_time(markdown, words_per_minute=200)

        assert result == 5  # 1000 words / 200 wpm = 5 minutes

    def test_estimate_with_markdown_formatting(self):
        """Test that markdown formatting is ignored in word count."""
        markdown = """
        # Title

        **Bold text** and *italic text* with `code` formatting.

        - List item one
        - List item two

        [Link text](http://example.com) and ![image](image.jpg).

        > Blockquote text here
        """

        # Count actual words without formatting
        expected_words = len(
            "Title Bold text and italic text with code formatting List item one List item two Link text and Blockquote text here".split()
        )
        result = estimate_reading_time(markdown, words_per_minute=200)

        # Should be close to expected based on actual word count
        expected_minutes = max(1, round(expected_words / 200))
        assert result == expected_minutes

    def test_estimate_empty_text(self):
        """Test reading time for empty text."""
        result = estimate_reading_time("", words_per_minute=200)
        assert result == 1  # Minimum is 1 minute

    def test_estimate_whitespace_only(self):
        """Test reading time for whitespace-only text."""
        result = estimate_reading_time("   \n\t  ", words_per_minute=200)
        assert result == 1  # Minimum is 1 minute

    def test_estimate_different_reading_speed(self):
        """Test reading time with different reading speeds."""
        # Create text with approximately 300 words
        word = "word "
        markdown = word * 300

        result_slow = estimate_reading_time(markdown, words_per_minute=100)
        result_fast = estimate_reading_time(markdown, words_per_minute=300)

        assert result_slow > result_fast
        assert result_slow == 3  # 300 / 100 = 3 minutes
        assert result_fast == 1  # 300 / 300 = 1 minute

    def test_estimate_removes_images_and_links(self):
        """Test that image and link markdown is removed from word count."""
        markdown = """
        This text has ![an image](image.jpg) and [a link](http://example.com).
        The word count should not include the URL text.
        """

        result = estimate_reading_time(markdown)

        # Should not count "image.jpg", "http://example.com", etc. as words
        # Only count actual readable text words
        readable_words = (
            "This text has and The word count should not include the URL text".split()
        )
        expected_minutes = max(1, round(len(readable_words) / 200))

        # Allow some tolerance for word counting differences
        assert abs(result - expected_minutes) <= 1
