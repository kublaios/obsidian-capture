"""Unit tests for metadata extraction fallback."""

from src.obsidian_capture.metadata import (
    ArticleMetadata,
    clean_metadata_text,
    extract_author,
    extract_canonical_url,
    extract_description,
    extract_keywords,
    extract_metadata_from_html,
    extract_published_date,
    extract_site_name,
    extract_title,
    generate_fallback_slug,
)


class TestArticleMetadata:
    """Test ArticleMetadata dataclass."""

    def test_to_dict_with_all_fields(self):
        """Test conversion to dict with all fields populated."""
        metadata = ArticleMetadata(
            title="Test Title",
            author="Test Author",
            published_at="2023-10-15T10:00:00",
            description="Test description",
            keywords="test, keywords",
            canonical_url="https://example.com/article",
            site_name="Example Site",
        )

        result = metadata.to_dict()

        assert result == {
            "title": "Test Title",
            "author": "Test Author",
            "published_at": "2023-10-15T10:00:00",
            "description": "Test description",
            "keywords": "test, keywords",
            "canonical_url": "https://example.com/article",
            "site_name": "Example Site",
        }

    def test_to_dict_with_none_values(self):
        """Test conversion to dict excludes None values."""
        metadata = ArticleMetadata(
            title="Test Title",
            author=None,
            published_at="2023-10-15T10:00:00",
            description=None,
        )

        result = metadata.to_dict()

        assert result == {"title": "Test Title", "published_at": "2023-10-15T10:00:00"}

    def test_to_dict_empty(self):
        """Test conversion to dict with all None values."""
        metadata = ArticleMetadata()
        result = metadata.to_dict()
        assert result == {}


class TestCleanMetadataText:
    """Test metadata text cleaning."""

    def test_clean_normal_text(self):
        """Test cleaning normal text."""
        result = clean_metadata_text("Hello World")
        assert result == "Hello World"

    def test_clean_whitespace(self):
        """Test cleaning excessive whitespace."""
        result = clean_metadata_text("  Hello   World  \n\t ")
        assert result == "Hello World"

    def test_clean_control_characters(self):
        """Test removing control characters."""
        text_with_control = "Hello\x00World\x1f\x7f\x9fTest"
        result = clean_metadata_text(text_with_control)
        assert result == "HelloWorld Test"

    def test_clean_empty_text(self):
        """Test cleaning empty text."""
        result = clean_metadata_text("")
        assert result == ""

    def test_clean_none_text(self):
        """Test cleaning None text."""
        result = clean_metadata_text(None)
        assert result == ""

    def test_clean_whitespace_only(self):
        """Test cleaning whitespace-only text."""
        result = clean_metadata_text("   \n\t  ")
        assert result == ""


class TestExtractTitle:
    """Test title extraction with fallbacks."""

    def test_extract_title_from_og_title(self):
        """Test extracting title from Open Graph meta tag."""
        html = '<meta property="og:title" content="OG Title">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result == "OG Title"

    def test_extract_title_from_twitter_title(self):
        """Test extracting title from Twitter meta tag when OG not available."""
        html = '<meta name="twitter:title" content="Twitter Title">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result == "Twitter Title"

    def test_extract_title_from_h1(self):
        """Test extracting title from H1 when meta tags not available."""
        html = "<h1>H1 Title</h1>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result == "H1 Title"

    def test_extract_title_from_title_tag(self):
        """Test extracting title from title tag as final fallback."""
        html = "<title>Page Title</title>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result == "Page Title"

    def test_extract_title_with_article_title_class(self):
        """Test extracting title from article-title class."""
        html = '<div class="article-title">Article Title</div>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result == "Article Title"

    def test_extract_title_precedence_order(self):
        """Test that Open Graph takes precedence over other methods."""
        html = """
        <meta property="og:title" content="OG Title">
        <meta name="twitter:title" content="Twitter Title">
        <h1>H1 Title</h1>
        <title>Page Title</title>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result == "OG Title"

    def test_extract_title_no_content(self):
        """Test title extraction when no title sources available."""
        html = "<div>No title here</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result is None

    def test_extract_title_empty_content(self):
        """Test title extraction when sources have empty content."""
        html = """
        <meta property="og:title" content="">
        <h1></h1>
        <title>   </title>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_title(soup)
        assert result is None


class TestExtractAuthor:
    """Test author extraction with fallbacks."""

    def test_extract_author_from_rel_author(self):
        """Test extracting author from rel=author link."""
        html = '<a rel="author">John Doe</a>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result == "John Doe"

    def test_extract_author_from_author_class(self):
        """Test extracting author from author class."""
        html = '<span class="author">Jane Smith</span>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result == "Jane Smith"

    def test_extract_author_from_byline_class(self):
        """Test extracting author from byline class."""
        html = '<div class="byline">By Bob Wilson</div>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result == "By Bob Wilson"

    def test_extract_author_from_meta_tag(self):
        """Test extracting author from meta tag when selectors fail."""
        html = '<meta name="author" content="Meta Author">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result == "Meta Author"

    def test_extract_author_from_article_author_meta(self):
        """Test extracting author from article:author meta tag."""
        html = '<meta property="article:author" content="Article Author">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result == "Article Author"

    def test_extract_author_precedence(self):
        """Test that selector-based extraction takes precedence over meta tags."""
        html = """
        <span class="author">Class Author</span>
        <meta name="author" content="Meta Author">
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result == "Class Author"

    def test_extract_author_no_author_found(self):
        """Test author extraction when no author found."""
        html = "<div>No author here</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_author(soup)
        assert result is None


class TestExtractPublishedDate:
    """Test published date extraction with fallbacks."""

    def test_extract_date_from_time_datetime(self):
        """Test extracting date from time element with datetime attribute."""
        html = '<time datetime="2023-10-15T14:30:00Z">October 15, 2023</time>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result == "2023-10-15T14:30:00+00:00"

    def test_extract_date_from_og_published_time(self):
        """Test extracting date from Open Graph published time."""
        html = '<meta property="article:published_time" content="2023-10-15T10:00:00Z">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result == "2023-10-15T10:00:00+00:00"

    def test_extract_date_from_published_class(self):
        """Test extracting date from published class text content."""
        html = '<span class="published">October 15, 2023</span>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result is not None
        assert "2023-10-15" in result

    def test_extract_date_from_date_class(self):
        """Test extracting date from date class."""
        html = '<div class="date">2023-10-15</div>'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result is not None
        assert "2023-10-15" in result

    def test_extract_date_invalid_datetime_continues(self):
        """Test that invalid datetime doesn't stop processing."""
        html = """
        <time datetime="invalid-date">Invalid</time>
        <div class="date">2023-10-15</div>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result is not None
        assert "2023-10-15" in result

    def test_extract_date_invalid_og_time_continues(self):
        """Test that invalid OG time doesn't stop processing."""
        html = """
        <meta property="article:published_time" content="not-a-date">
        <span class="published">October 15, 2023</span>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result is not None
        assert "2023-10-15" in result

    def test_extract_date_unparseable_text_continues(self):
        """Test that unparseable text continues to next selector."""
        html = """
        <div class="published">Not a date</div>
        <span class="date">2023-10-15</span>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result is not None
        assert "2023-10-15" in result

    def test_extract_date_no_date_found(self):
        """Test date extraction when no date found."""
        html = "<div>No date here</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_published_date(soup)
        assert result is None


class TestExtractDescription:
    """Test description extraction with fallbacks."""

    def test_extract_description_from_og(self):
        """Test extracting description from Open Graph meta tag."""
        html = '<meta property="og:description" content="OG Description">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_description(soup)
        assert result == "OG Description"

    def test_extract_description_from_meta(self):
        """Test extracting description from meta description."""
        html = '<meta name="description" content="Meta Description">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_description(soup)
        assert result == "Meta Description"

    def test_extract_description_from_twitter(self):
        """Test extracting description from Twitter meta tag."""
        html = '<meta name="twitter:description" content="Twitter Description">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_description(soup)
        assert result == "Twitter Description"

    def test_extract_description_precedence(self):
        """Test description extraction precedence order."""
        html = """
        <meta property="og:description" content="OG Description">
        <meta name="description" content="Meta Description">
        <meta name="twitter:description" content="Twitter Description">
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_description(soup)
        assert result == "OG Description"

    def test_extract_description_no_description(self):
        """Test description extraction when no description found."""
        html = "<div>No description here</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_description(soup)
        assert result is None


class TestExtractKeywords:
    """Test keywords extraction with fallbacks."""

    def test_extract_keywords_from_meta(self):
        """Test extracting keywords from meta keywords tag."""
        html = '<meta name="keywords" content="test, keywords, meta">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_keywords(soup)
        assert result == "test, keywords, meta"

    def test_extract_keywords_from_tags_class(self):
        """Test extracting keywords from tags class elements."""
        html = """
        <div class="tags">
            <a href="#">tag1</a>
            <a href="#">tag2</a>
            <a href="#">tag3</a>
        </div>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_keywords(soup)
        assert result == "tag1, tag2, tag3"

    def test_extract_keywords_from_categories(self):
        """Test extracting keywords from categories class elements."""
        html = """
        <div class="categories">
            <a href="#">cat1</a>
            <a href="#">cat2</a>
        </div>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_keywords(soup)
        assert result == "cat1, cat2"

    def test_extract_keywords_limit_to_ten(self):
        """Test that keywords are limited to first 10 tags."""
        html_tags = "".join([f'<a class="tag">tag{i}</a>' for i in range(15)])
        html = f"<div>{html_tags}</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_keywords(soup)
        tags = result.split(", ")
        assert len(tags) <= 10

    def test_extract_keywords_avoid_duplicates(self):
        """Test that duplicate keywords are avoided."""
        html = """
        <div class="tags">
            <a href="#">duplicate</a>
            <a href="#">duplicate</a>
            <a href="#">unique</a>
        </div>
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_keywords(soup)
        assert result == "duplicate, unique"

    def test_extract_keywords_no_keywords(self):
        """Test keywords extraction when no keywords found."""
        html = "<div>No keywords here</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_keywords(soup)
        assert result is None


class TestExtractCanonicalUrl:
    """Test canonical URL extraction with fallbacks."""

    def test_extract_canonical_from_link(self):
        """Test extracting canonical URL from link tag."""
        html = '<link rel="canonical" href="https://example.com/canonical">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_canonical_url(soup, "https://example.com/source")
        assert result == "https://example.com/canonical"

    def test_extract_canonical_from_og_url(self):
        """Test extracting canonical URL from Open Graph URL."""
        html = '<meta property="og:url" content="https://example.com/og-url">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_canonical_url(soup, "https://example.com/source")
        assert result == "https://example.com/og-url"

    def test_extract_canonical_fallback_to_source(self):
        """Test falling back to source URL when no canonical found."""
        html = "<div>No canonical URL here</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_canonical_url(soup, "https://example.com/source")
        assert result == "https://example.com/source"

    def test_extract_canonical_precedence(self):
        """Test canonical URL extraction precedence."""
        html = """
        <link rel="canonical" href="https://example.com/canonical">
        <meta property="og:url" content="https://example.com/og-url">
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_canonical_url(soup, "https://example.com/source")
        assert result == "https://example.com/canonical"


class TestExtractSiteName:
    """Test site name extraction with fallbacks."""

    def test_extract_site_name_from_og(self):
        """Test extracting site name from Open Graph meta tag."""
        html = '<meta property="og:site_name" content="Example Site">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_site_name(soup, "https://example.com/page")
        assert result == "Example Site"

    def test_extract_site_name_from_app_name(self):
        """Test extracting site name from application-name meta tag."""
        html = '<meta name="application-name" content="App Name">'
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_site_name(soup, "https://example.com/page")
        assert result == "App Name"

    def test_extract_site_name_from_domain(self):
        """Test extracting site name from URL domain."""
        html = "<div>No site name meta</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_site_name(soup, "https://example.com/page")
        assert result == "example.com"

    def test_extract_site_name_removes_www(self):
        """Test that www prefix is removed from domain."""
        html = "<div>No site name meta</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_site_name(soup, "https://www.example.com/page")
        assert result == "example.com"

    def test_extract_site_name_invalid_url(self):
        """Test site name extraction with invalid URL."""
        html = "<div>No site name meta</div>"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        result = extract_site_name(soup, "not-a-url")
        assert result is None


class TestGenerateFallbackSlug:
    """Test fallback slug generation."""

    def test_generate_slug_from_title(self):
        """Test generating slug from title when available."""
        result = generate_fallback_slug("https://example.com", "Test Title")
        assert result == "test-title"

    def test_generate_slug_from_url_path(self):
        """Test generating slug from URL path when no title."""
        result = generate_fallback_slug("https://example.com/article/test-page", None)
        assert result == "article-test-page"

    def test_generate_slug_removes_file_extensions(self):
        """Test that common file extensions are removed."""
        result = generate_fallback_slug("https://example.com/article.html", None)
        assert result == "article"

    def test_generate_slug_from_domain_fallback(self):
        """Test generating slug from domain as final fallback."""
        result = generate_fallback_slug("https://example.com", None)
        assert result == "example-com"

    def test_generate_slug_removes_www(self):
        """Test that www is removed from domain slug."""
        result = generate_fallback_slug("https://www.example.com", None)
        assert result == "example-com"

    def test_generate_slug_final_fallback(self):
        """Test final fallback to 'article'."""
        result = generate_fallback_slug("", None)
        assert result == "article"

    def test_generate_slug_invalid_url(self):
        """Test slug generation with invalid URL."""
        result = generate_fallback_slug("not-a-url", None)
        assert result == "not-a-url"

    def test_generate_slug_empty_title_uses_url(self):
        """Test that empty title falls back to URL."""
        result = generate_fallback_slug("https://example.com/test-page", "")
        assert result == "test-page"

    def test_generate_slug_long_path(self):
        """Test slug generation with long URL path."""
        url = "https://example.com/very/long/path/to/article/page"
        result = generate_fallback_slug(url, None)
        assert len(result) <= 50
        assert "very-long-path" in result


class TestExtractMetadataFromHtml:
    """Test complete metadata extraction."""

    def test_extract_metadata_complete(self):
        """Test extracting complete metadata."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Test Article">
            <meta name="author" content="John Doe">
            <meta property="article:published_time" content="2023-10-15T10:00:00Z">
            <meta property="og:description" content="Test description">
            <meta name="keywords" content="test, article">
            <link rel="canonical" href="https://example.com/canonical">
            <meta property="og:site_name" content="Example Site">
        </head>
        <body>Content</body>
        </html>
        """

        result = extract_metadata_from_html(html, "https://example.com/source")

        assert result.title == "Test Article"
        assert result.author == "John Doe"
        assert "2023-10-15T10:00:00" in result.published_at
        assert result.description == "Test description"
        assert result.keywords == "test, article"
        assert result.canonical_url == "https://example.com/canonical"
        assert result.site_name == "Example Site"

    def test_extract_metadata_with_fallbacks(self):
        """Test metadata extraction using fallbacks."""
        html = """
        <html>
        <head>
            <title>Fallback Title</title>
        </head>
        <body>
            <div class="author">Fallback Author</div>
            <span class="date">2023-10-15</span>
        </body>
        </html>
        """

        result = extract_metadata_from_html(html, "https://example.com/source")

        assert result.title == "Fallback Title"
        assert result.author == "Fallback Author"
        assert "2023-10-15" in result.published_at
        assert result.canonical_url == "https://example.com/source"
        assert result.site_name == "example.com"

    def test_extract_metadata_invalid_html(self):
        """Test metadata extraction with invalid HTML."""
        result = extract_metadata_from_html(None, "https://example.com")

        assert isinstance(result, ArticleMetadata)
        assert result.title is None
        assert result.author is None
        assert result.published_at is None

    def test_extract_metadata_empty_html(self):
        """Test metadata extraction with empty HTML."""
        result = extract_metadata_from_html("", "https://example.com")

        assert isinstance(result, ArticleMetadata)
        # Should still extract site name from URL
        assert result.site_name == "example.com"
        assert result.canonical_url == "https://example.com"
