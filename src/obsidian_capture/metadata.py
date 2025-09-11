"""Metadata extraction from HTML content."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag
from dateutil.parser import ParserError
from dateutil.parser import parse as parse_date
from slugify import slugify

from .extract import extract_element_by_selector, get_clean_text_content


def safe_get_attr(element: Any, attr: str) -> Optional[str]:
    """Safely get an attribute from a BeautifulSoup element."""
    if element and isinstance(element, Tag):
        value = element.get(attr)
        if isinstance(value, str):
            return value
    return None


@dataclass
class ArticleMetadata:
    """Extracted article metadata."""

    title: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    site_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for field, value in [
            ("title", self.title),
            ("author", self.author),
            ("published_at", self.published_at),
            ("description", self.description),
            ("keywords", self.keywords),
            ("canonical_url", self.canonical_url),
            ("site_name", self.site_name),
        ]:
            if value is not None:
                result[field] = value
        return result


def extract_metadata_from_html(html_content: str, source_url: str) -> ArticleMetadata:
    """
    Extract metadata from HTML content.

    Args:
        html_content: Raw HTML content
        source_url: Original URL for fallback metadata

    Returns:
        Extracted metadata
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except Exception:
        return ArticleMetadata()

    metadata = ArticleMetadata()

    # Extract title
    metadata.title = extract_title(soup)

    # Extract author
    metadata.author = extract_author(soup)

    # Extract published date
    metadata.published_at = extract_published_date(soup)

    # Extract description
    metadata.description = extract_description(soup)

    # Extract keywords
    metadata.keywords = extract_keywords(soup)

    # Extract canonical URL
    metadata.canonical_url = extract_canonical_url(soup, source_url)

    # Extract site name
    metadata.site_name = extract_site_name(soup, source_url)

    return metadata


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract article title from various sources."""
    # Try Open Graph title (highest priority)
    og_title = soup.find("meta", attrs=cast(Dict[str, Any], {"property": "og:title"}))
    content = safe_get_attr(og_title, "content")
    if content:
        return clean_metadata_text(content)

    # Try Twitter title
    twitter_title = soup.find(
        "meta", attrs=cast(Dict[str, Any], {"name": "twitter:title"})
    )
    content = safe_get_attr(twitter_title, "content")
    if content:
        return clean_metadata_text(content)

    # Try other common meta title patterns
    meta_selectors = [
        {"name": "title"},  # Generic meta title
        {"property": "article:title"},  # Article-specific OpenGraph
        {"name": "headline"},  # Some news sites use this
        {"name": "sailthru.title"},  # Sailthru CMS
    ]
    for meta_selector in meta_selectors:
        meta_title = soup.find("meta", attrs=cast(Dict[str, Any], meta_selector))
        content = safe_get_attr(meta_title, "content")
        if content:
            return clean_metadata_text(content)

    # Try article title selectors (expanded list)
    title_selectors = [
        "h1",  # Most common article title
        ".article-title",  # Common article title class
        ".post-title",  # Blog post title class
        ".entry-title",  # Entry/article title class
        ".page-title",  # Page title class
        ".story-title",  # News story title class
        ".content-title",  # Content title class
        "header h1",  # Header H1 (common in articles)
        "article h1",  # Article H1
        ".title",  # Generic title class
        "title",  # HTML title tag (last resort)
    ]

    for selector in title_selectors:
        element = extract_element_by_selector(soup, selector)
        if element:
            title = get_clean_text_content(element)
            if title and len(title.strip()) > 0:
                return clean_metadata_text(title)

    return None


def extract_author(soup: BeautifulSoup) -> Optional[str]:
    """Extract author information."""
    # Try structured data
    for selector in ['[rel="author"]', ".author", ".byline", ".writer"]:
        element = extract_element_by_selector(soup, selector)
        if element:
            author = get_clean_text_content(element)
            if author:
                return clean_metadata_text(author)

    # Try meta tags
    for meta_name in ["author", "article:author"]:
        meta = soup.find(
            "meta", attrs=cast(Dict[str, Any], {"name": meta_name})
        ) or soup.find("meta", attrs=cast(Dict[str, Any], {"property": meta_name}))
        content = safe_get_attr(meta, "content")
        if content:
            return clean_metadata_text(content)

    return None


def extract_published_date(soup: BeautifulSoup) -> Optional[str]:
    """Extract published date in ISO format."""
    # Try structured data with datetime attributes
    for selector in ["time[datetime]", "[datetime]"]:
        element = extract_element_by_selector(soup, selector)
        datetime_attr = safe_get_attr(element, "datetime")
        if datetime_attr:
            try:
                dt: datetime = parse_date(datetime_attr)
                return dt.isoformat()
            except ParserError:
                continue

    # Try Open Graph published time
    og_published = soup.find(
        "meta", attrs=cast(Dict[str, Any], {"property": "article:published_time"})
    )
    content = safe_get_attr(og_published, "content")
    if content:
        try:
            dt_og: datetime = parse_date(content)
            return dt_og.isoformat()
        except ParserError:
            pass

    # Try common date selectors and parse text content
    for selector in [".published", ".date", ".post-date", ".entry-date"]:
        element = extract_element_by_selector(soup, selector)
        if element:
            date_text = get_clean_text_content(element)
            if date_text:
                try:
                    dt_text: datetime = parse_date(date_text)
                    return dt_text.isoformat()
                except ParserError:
                    continue

    return None


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract article description/summary."""
    # Try Open Graph description
    og_desc = soup.find(
        "meta", attrs=cast(Dict[str, Any], {"property": "og:description"})
    )
    content = safe_get_attr(og_desc, "content")
    if content:
        return clean_metadata_text(content)

    # Try meta description
    meta_desc = soup.find("meta", attrs=cast(Dict[str, Any], {"name": "description"}))
    content = safe_get_attr(meta_desc, "content")
    if content:
        return clean_metadata_text(content)

    # Try Twitter description
    twitter_desc = soup.find(
        "meta", attrs=cast(Dict[str, Any], {"name": "twitter:description"})
    )
    content = safe_get_attr(twitter_desc, "content")
    if content:
        return clean_metadata_text(content)

    return None


def extract_keywords(soup: BeautifulSoup) -> Optional[str]:
    """Extract keywords/tags."""
    # Try meta keywords
    meta_keywords = soup.find("meta", attrs=cast(Dict[str, Any], {"name": "keywords"}))
    content = safe_get_attr(meta_keywords, "content")
    if content:
        return clean_metadata_text(content)

    # Try article tags
    tag_elements = soup.select(".tags a, .tag, .categories a, .category")
    if tag_elements:
        tags = []
        for element in tag_elements[:10]:  # Limit to first 10 tags
            tag = get_clean_text_content(element)
            if tag and tag not in tags:
                tags.append(tag)
        if tags:
            return ", ".join(tags)

    return None


def extract_canonical_url(soup: BeautifulSoup, source_url: str) -> Optional[str]:
    """Extract canonical URL."""
    # Try link rel=canonical
    canonical_link = soup.find("link", rel="canonical")
    href = safe_get_attr(canonical_link, "href")
    if href:
        return href

    # Try Open Graph URL
    og_url = soup.find("meta", attrs=cast(Dict[str, Any], {"property": "og:url"}))
    content = safe_get_attr(og_url, "content")
    if content:
        return content

    # Fallback to source URL
    return source_url


def extract_site_name(soup: BeautifulSoup, source_url: str) -> Optional[str]:
    """Extract site name."""
    # Try Open Graph site name
    og_site = soup.find(
        "meta", attrs=cast(Dict[str, Any], {"property": "og:site_name"})
    )
    content = safe_get_attr(og_site, "content")
    if content:
        return clean_metadata_text(content)

    # Try application name
    app_name = soup.find(
        "meta", attrs=cast(Dict[str, Any], {"name": "application-name"})
    )
    content = safe_get_attr(app_name, "content")
    if content:
        return clean_metadata_text(content)

    # Fallback to domain from URL
    try:
        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc
        if domain:
            # Clean up common prefixes
            domain = re.sub(r"^www\.", "", domain)
            return domain
    except Exception:
        pass

    return None


def clean_metadata_text(text: str) -> str:
    """Clean metadata text content."""
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    return text


def generate_fallback_slug(url: str, title: Optional[str] = None) -> str:
    """
    Generate fallback slug from URL or title.

    Args:
        url: Source URL
        title: Optional title text

    Returns:
        URL-safe slug string
    """
    if title:
        # Use title if available
        slug = slugify(title, max_length=50)
        if slug:
            return slug

    # Fallback to URL path
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path

        # Remove common file extensions and clean path
        path = re.sub(r"\.(html|htm|php|asp|aspx|jsp)$", "", path)
        path = path.strip("/")

        if path:
            # Replace path separators and generate slug
            path_slug = path.replace("/", "-")
            slug = slugify(path_slug, max_length=50)
            if slug:
                return slug
    except Exception:
        pass

    # Final fallback
    try:
        domain = urlparse(url).netloc
        if domain:
            domain = re.sub(r"^www\.", "", domain)
            return slugify(domain, max_length=20) or "article"
    except Exception:
        pass

    return "article"


def generate_obsidian_tags(soup: BeautifulSoup, source_url: str) -> List[str]:
    """
    Generate Obsidian-style tags from SEO keywords or URL path.

    Args:
        soup: BeautifulSoup object of the HTML
        source_url: Original URL of the article

    Returns:
        List of Obsidian-style tags (with # prefix)
    """
    tags = []

    # Try to extract from SEO meta keywords first
    seo_tags = extract_seo_tags(soup)
    if seo_tags:
        tags.extend(seo_tags)

    # If no SEO tags found, generate from URL path
    if not tags:
        url_tags = extract_tags_from_url(source_url)
        tags.extend(url_tags)

    # Clean and format tags with # prefix
    obsidian_tags = []
    for tag in tags:
        clean_tag = clean_tag_text(tag)
        if clean_tag and len(clean_tag) > 2:  # Only words with more than 2 letters
            obsidian_tags.append(f"#{clean_tag}")

    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in obsidian_tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_tags.append(tag)

    return unique_tags


def extract_seo_tags(soup: BeautifulSoup) -> List[str]:
    """
    Extract tags from SEO meta keywords and article tags.

    Args:
        soup: BeautifulSoup object of the HTML

    Returns:
        List of extracted tags
    """
    tags = []

    # Try meta keywords first
    meta_keywords = soup.find("meta", attrs=cast(Dict[str, Any], {"name": "keywords"}))
    content = safe_get_attr(meta_keywords, "content")
    if content:
        # Split by common delimiters
        keyword_tags = re.split(r"[,;|]", content)
        for tag in keyword_tags:
            tag = tag.strip()
            if tag:
                tags.append(tag)

    # Try article tags/categories in page content
    if not tags:
        tag_elements = soup.select(
            ".tags a, .tag, .categories a, .category, .post-tags a, .article-tags a"
        )
        for element in tag_elements[:10]:  # Limit to first 10 tags
            tag_text = get_clean_text_content(element)
            if tag_text:
                tags.append(tag_text)

    return tags


def extract_tags_from_url(url: str) -> List[str]:
    """
    Extract tags from URL path, using the last path segment.

    Example: website.com/p/articles/how-to-encode-string
    Produces: ['how', 'encode', 'string']

    Args:
        url: Source URL

    Returns:
        List of extracted tags from URL path
    """
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path.strip("/")

        if not path:
            return []

        # Get the last path segment
        path_segments = path.split("/")
        last_segment = path_segments[-1] if path_segments else ""

        # Remove file extensions
        last_segment = re.sub(r"\.(html|htm|php|asp|aspx|jsp)$", "", last_segment)

        if not last_segment:
            return []

        # Split by dashes and underscores
        words = re.split(r"[-_]+", last_segment)

        # Clean and filter words
        tags = []
        for word in words:
            word = clean_tag_text(word)
            if word and len(word) > 2:  # Only words with more than 2 letters
                tags.append(word)

        return tags

    except Exception:
        return []


def clean_tag_text(text: str) -> str:
    """
    Clean tag text for use as Obsidian tag.

    Args:
        text: Raw tag text

    Returns:
        Cleaned tag text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower().strip()

    # Remove special characters, keep only alphanumeric and basic chars
    text = re.sub(r"[^\w\s-]", "", text)

    # Replace spaces and dashes with single dash
    text = re.sub(r"[\s-]+", "-", text)

    # Remove leading/trailing dashes
    text = text.strip("-")

    # Remove numbers-only tags
    if text.isdigit():
        return ""

    return text
