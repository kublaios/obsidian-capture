# HTML → Markdown Capture Tool for Obsidian Vault

A command-line tool for capturing web articles and local HTML files, converting them to Markdown files for your Obsidian vault. Automatically extracts content using configurable CSS selectors, preserves metadata, and organizes files in date-based directories.

## Features

- **Dual Input Support**: Process both remote URLs and local HTML files (perfect for paywall content)
- **Smart Content Extraction**: Uses configurable CSS selectors with fallback options
- **Intelligent Filename Generation**: Uses extracted article titles for human-readable filenames
- **Dry Run Preview**: Preview captures without writing files - see front matter and content length
- **Metadata Preservation**: Extracts title, author, publication date, and other metadata
- **Automatic Tag Generation**: Generates Obsidian-style tags from SEO keywords or URL structure
- **Obsidian Integration**: Creates properly formatted Markdown files with YAML frontmatter
- **Flexible Organization**: Date-based directories (YYYY-MM) with optional subfolders
- **Element Exclusion**: Remove unwanted elements like ads, footers, and navigation
- **Collision Handling**: Automatic filename collision resolution with numeric suffixes
- **Multiple Output Formats**: Human-readable text and machine-readable JSON output
- **Error Handling**: Comprehensive error handling with specific exit codes

## Installation

### Binary Releases (Recommended)
Download pre-built binaries from the [GitHub Releases](https://github.com/kublaios/obsidian-capture/releases) page:

- **Linux**: `obsidian-capture-linux-x86_64`
- **Windows**: `obsidian-capture-windows-x86_64.exe`
- **macOS Intel**: `obsidian-capture-macos-x86_64`
- **macOS Apple Silicon**: `obsidian-capture-macos-arm64`

Binary executables are standalone and don't require Python installation.

### Python Package Install
```bash
pip install obsidian-capture
```

### Development Install
```bash
# Clone the repository
git clone <repository-url>
cd obsidian-capture

# Install in development mode with dependencies
pip install -e .
```

### Production Install (when available)
```bash
pip install obsidian-capture
```

## Quick Start

### Basic Usage
```bash
# Capture a web article to your Obsidian vault
obsidian-capture https://example.com/article --vault /path/to/Vault

# Capture a local HTML file (great for paywall content)
obsidian-capture /path/to/saved-article.html --vault /path/to/Vault
obsidian-capture ~/Downloads/paywall-page.html --vault /path/to/Vault
```

### With Configuration File
```bash
# Use custom selectors and settings
obsidian-capture https://example.com/article \
  --vault /path/to/Vault \
  --config /path/to/config.yaml

# Or place config at ~/.obsidian-capture.yml for automatic discovery
obsidian-capture https://example.com/article \
  --vault /path/to/Vault

# With vault path in config file (no --vault needed)
obsidian-capture https://example.com/article \
  --config /path/to/config.yaml

# Add custom tags
obsidian-capture https://example.com/article \
  --tags "tutorial,important"
```

## Local HTML File Support

The tool supports processing local HTML files in addition to remote URLs, making it perfect for handling content behind paywalls or for offline processing.

### When to Use Local Files

- **Paywall Content**: Save the full article as HTML when it's behind a paywall, then process it locally
- **Offline Processing**: Process saved HTML files without internet connectivity  
- **Archive Processing**: Bulk process HTML files from web archives or backups
- **Development/Testing**: Test extraction rules on local HTML samples

### Usage Examples

```bash
# Process a single local HTML file
obsidian-capture /path/to/article.html --vault ~/ObsidianVault

# Process with custom configuration
obsidian-capture ~/Downloads/saved-article.html \
  --vault ~/ObsidianVault \
  --config ~/.obsidian-capture.yml \
  --tags "paywall,premium"

# Preview local file processing
obsidian-capture /tmp/test-article.html --vault ~/vault --dry

# Process with custom tags and subfolder
obsidian-capture "./saved-pages/important-article.html" \
  --vault ~/ObsidianVault \
  --subfolder "premium-content" \
  --tags "research,important"
```

### How It Works

1. **Automatic Detection**: The tool automatically detects whether the input is a URL or file path
2. **File Validation**: Checks that the file exists and is readable
3. **Size Limits**: Applies the same size limits as remote URLs (configurable)
4. **Encoding Support**: Handles various text encodings (UTF-8, Latin-1, CP1252)
5. **Same Processing**: Uses identical extraction, conversion, and metadata processing as URLs

### Saving Pages for Local Processing

**Browser Save Options:**
- **Chrome/Edge**: Right-click → "Save as" → "Webpage, Complete" or "Webpage, HTML Only"
- **Firefox**: Ctrl+S → "Web Page, complete" or "Web Page, HTML only"  
- **Safari**: File → Export As → "Web Archive" or use Developer tools to save HTML

**Command Line Tools:**
```bash
# Using wget
wget -O article.html "https://example.com/paywall-article"

# Using curl  
curl -o article.html "https://example.com/paywall-article"

# Using browser automation tools like Playwright/Selenium for complex sites
```

### Tips for Best Results

- **Save Complete Pages**: When possible, save "complete" HTML to include embedded resources
- **Verify Content**: Check that the saved HTML contains the full article content
- **Consistent Naming**: Use descriptive filenames for better organization
- **Batch Processing**: Process multiple files in a directory with shell loops

## Configuration

Create a configuration file to customize content extraction. The tool automatically looks for `~/.obsidian-capture.yml` if no config is specified.

```yaml
# ~/.obsidian-capture.yml or config.yaml

# Vault path (optional - can also use --vault)
# Supports absolute paths, relative paths, and tilde expansion
vault: "~/Documents/ObsidianVault"  # Tilde expansion
# vault: "./my-vault"               # Relative to current directory  
# vault: "/absolute/path/to/vault"  # Absolute path

# Content extraction selectors (required)
selectors:
  - 'article'
  - 'main'
  - '[role="main"]'
  - '.content'
  - '.post-content'
  - '.entry-content'
  - '.article-content'
  - 'body'

# Content settings
min_content_chars: 80
overwrite: false
subfolder: "web-articles"

# Remove unwanted elements
exclusion_selectors:
  - "footer"
  - ".advertisement"
  - ".subscribe-offer"
  - "#comments"

# Default tags (merged with auto-generated tags)
tags:
  - "web"
  - "archived"

# Exclude fields from front matter (optional)
exclude_fields:
  - "canonical_url"              # Remove canonical URL
  - "keywords"                   # Remove SEO keywords  
  - "selector"                   # Remove CSS selector used
```

## Automatic Tag Generation

The tool automatically generates Obsidian-style tags for every captured article using multiple sources:

### Tag Sources (in priority order)

1. **Config File Tags**: Default tags from your configuration
2. **CLI Tags**: Tags specified via `--tags` option
3. **SEO Keywords**: Extracted from `<meta name="keywords">` or article tag elements
4. **URL Path Tags**: Generated from URL structure as fallback

### Usage Examples

```bash
# Add custom tags via command line
obsidian-capture https://example.com/article \
  --vault /path/to/vault \
  --tags "tutorial,python,advanced"

# URL-based tag generation fallback
# https://blog.com/articles/how-to-learn-machine-learning
# Generates: #how #learn #machine #learning

# SEO keyword extraction
# <meta name="keywords" content="python, programming, tutorial">
# Generates: #python #programming #tutorial
```

### Tag Processing Rules

- **Obsidian Format**: All tags are prefixed with `#` (e.g., `#python`, `#tutorial`)
- **Length Filter**: Only words with more than 2 characters become tags
- **Deduplication**: Duplicate tags are automatically removed (case-insensitive)
- **URL Fallback**: If no SEO keywords found, generates from last URL path segment
- **Smart Cleaning**: Removes special characters and normalizes tag format

### Combined Tag Example

With config file containing `tags: ["web", "archived"]`, CLI tags `--tags "tutorial,python"`, and URL `https://blog.com/how-to-code-python`, the final tags would be:

```yaml
tags:
  - "#web"          # From config
  - "#archived"     # From config  
  - "#tutorial"     # From CLI
  - "#python"       # From CLI
  - "#how"          # From URL (fallback)
  - "#code"         # From URL (fallback)
```

## Intelligent Filename Generation

The tool automatically generates human-readable filenames based on extracted article titles, with smart fallbacks for better file organization.

### How It Works

1. **Title-Based Naming**: Extracts article titles and converts them to filesystem-safe filenames
2. **Multiple Title Sources**: Uses comprehensive title extraction from various HTML elements
3. **URL Fallback**: Uses URL structure when no title is available  
4. **Length Management**: Automatically truncates long titles to reasonable lengths
5. **Collision Handling**: Adds numeric suffixes (-1, -2, etc.) for duplicate filenames

### Title Extraction Sources (in priority order)

1. **OpenGraph title** (`<meta property="og:title" content="...">`) - **Highest Priority**
2. **Twitter title** (`<meta name="twitter:title" content="...">`)  
3. **Other meta titles** (`<meta name="title">`, `<meta property="article:title">`)
4. **Article title classes** (`.article-title`, `.post-title`, `.entry-title`)
5. **Page title classes** (`.page-title`, `.story-title`, `.content-title`)
6. **Header elements** (`header h1`, `article h1`, `h1`)
7. **Generic title** (`.title`)
8. **HTML title tag** (`<title>` - last resort)

### Examples

```bash
# OpenGraph meta title (highest priority)
# <meta property="og:title" content="Swift Observations AsyncSequence for State Changes">
# Generated filename: swift-observations-asyncsequence-for-state-changes.md

# Article title: "How to Learn Python Programming"
# Generated filename: how-to-learn-python-programming.md

# Article title: "React & Vue.js: A Developer's Guide!"  
# Generated filename: react-vue-js-a-developer-s-guide.md

# No title found, URL: https://blog.com/articles/machine-learning-basics
# Generated filename: articles-machine-learning-basics.md

# Long title (truncated): "this-is-a-very-long-article-title-that-gets-truncated.md"
```

### Benefits

- **Human-Readable**: Filenames reflect actual article content
- **Obsidian-Friendly**: Easy to find and reference articles by name
- **Consistent**: Predictable naming scheme across all captures
- **Safe**: All special characters converted to filesystem-safe alternatives
- **Organized**: Better file organization in your vault

## Dry Run Preview

Preview what would be captured without actually writing any files. Perfect for testing configurations, verifying content extraction, and previewing metadata.

### Usage

```bash
# Basic dry run - preview capture without writing files
obsidian-capture https://example.com/article --dry

# Dry run with local HTML file
obsidian-capture /path/to/saved-article.html --dry

# Dry run with custom configuration
obsidian-capture https://example.com/article --dry --config my-config.yaml

# Dry run local file with additional tags
obsidian-capture ~/Downloads/paywall-article.html --dry --tags "important,bookmark"

# JSON output for scripting
obsidian-capture https://example.com/article --dry --format json
```

### What You'll See

**Text Output:**
```
🔍 DRY RUN PREVIEW
==================================================
📄 Proposed filename: how-to-learn-python-programming.md
🎯 Selector used: article
📊 Content length: 2,347 characters
⏱️  Processing time: 1,240ms

📋 FRONT MATTER PREVIEW:
---
title: How to Learn Python Programming
source: https://example.com/python-guide
author: John Doe
published_at: 2024-01-15T10:00:00Z
retrieved_at: 2024-01-15T12:30:15Z
tags:
  - "#python"
  - "#tutorial"
  - "#programming"
selector: article
---

✨ This was a preview only - no files were written.
   Remove --dry to actually capture the article.
```

**JSON Output:**
```json
{
  "status": "dry_run_preview",
  "url": "https://example.com/python-guide",
  "proposed_filename": "how-to-learn-python-programming.md",
  "selector_used": "article",
  "content_stats": {
    "extracted_chars": 2500,
    "markdown_chars": 2347
  },
  "elapsed_ms": 1240,
  "front_matter": {
    "title": "How to Learn Python Programming",
    "tags": ["#python", "#tutorial"]
  }
}
```

### Benefits

- **Safe Testing**: Verify configurations without creating files
- **Content Preview**: See exactly what content would be extracted
- **Metadata Review**: Check front matter before committing to capture
- **Performance Insights**: See processing time and content statistics
- **Debugging**: Identify issues with selectors or configuration

## Front Matter Field Exclusion

Control which fields appear in the YAML front matter of captured articles by excluding unwanted metadata fields.

### Usage

```yaml
# In your config file
exclude_fields:
  - "canonical_url"              # Remove canonical URL from front matter
  - "keywords"                   # Remove SEO keywords from front matter  
  - "selector"                   # Remove CSS selector from front matter
  - "description"                # Remove meta description
  - "site_name"                  # Remove site name
```

### Common Fields to Exclude

- **`canonical_url`**: The canonical URL of the article (often redundant with `source`)
- **`keywords`**: SEO keywords (may prefer auto-generated tags instead)  
- **`selector`**: CSS selector used for content extraction (technical detail)
- **`description`**: Meta description (may be too verbose for front matter)
- **`site_name`**: Website name (may prefer domain from URL)
- **`published_at`**: Publication date (if you don't need this metadata)
- **`author`**: Article author (if not relevant to your workflow)

### Before and After Example

**Without `exclude_fields` (default):**
```yaml
---
title: How to Learn Python Programming
source: https://blog.example.com/python-tutorial
canonical_url: https://blog.example.com/python-tutorial
keywords: python, programming, tutorial, beginner
selector: article
description: A comprehensive guide to learning Python programming
site_name: Example Blog
author: John Doe
published_at: 2024-01-15T10:00:00Z
retrieved_at: 2024-01-15T12:00:00Z
tags:
  - "#tutorial"
  - "#python"
---
```

**With `exclude_fields: ["canonical_url", "keywords", "selector"]`:**
```yaml
---
title: How to Learn Python Programming
source: https://blog.example.com/python-tutorial
description: A comprehensive guide to learning Python programming
site_name: Example Blog
author: John Doe
published_at: 2024-01-15T10:00:00Z
retrieved_at: 2024-01-15T12:00:00Z
tags:
  - "#tutorial"
  - "#python"
---
```

## Exclusion Selectors

Remove unwanted elements like ads, footers, and navigation from captured content using CSS selectors:

### Usage
```bash
# Remove footer and ads via command line
obsidian-capture https://example.com/article \
  --vault /path/to/vault \
  --exclude-selectors "footer,.advertisement,.subscribe-offer"

# Or configure in YAML file
exclusion_selectors:
  - "footer"
  - ".advertisement" 
  - ".subscribe-offer"
  - "#comments"
  - "nav"
```

### Features & Safeguards
- **Element Removal**: Removes matching elements before content extraction
- **Protected Elements**: Cannot remove `<html>` or `<body>` tags (protected roots)
- **Selector Limit**: Maximum 100 selectors to prevent performance issues
- **High Removal Warning**: Warns if >40% of elements are removed
- **Empty Content Detection**: Warns if primary content becomes empty after exclusions
- **Performance Monitoring**: Tracks exclusion processing time

### Warnings & Diagnostics
The tool provides comprehensive feedback:
```
INFO: Exclusion summary: 3/4 selectors successful, 15 elements removed (12.5% of document)
WARNING: High removal ratio detected: 45.2% of elements removed (89/197)
WARNING: Primary content elements (article, main) appear to be empty after exclusions
```

### Best Practices
- Start with common elements: `footer`, `nav`, `.advertisement`
- Use specific selectors to avoid removing important content
- Monitor warnings to ensure content quality
- Test selectors on sample pages before batch processing

## Command Line Options

```bash
obsidian-capture <URL_OR_PATH> [OPTIONS]

Arguments:
  URL_OR_PATH         URL of the article to capture OR path to local HTML file

Options:
  --vault PATH        Path to Obsidian vault directory (supports absolute, relative, and ~ paths; can be in config file)
  --config PATH       Path to configuration file (YAML)
  --tags TAGS         Additional tags to add (comma-separated, auto-formatted with #)
  --dry               Preview capture without writing files (shows front matter & content stats)
  --format FORMAT     Output format: text (default) or json
  --overwrite         Overwrite existing files
  --subfolder NAME    Subfolder within vault for organization
  --exclude-selectors CSS selectors for elements to remove (can be repeated)
  --timeout SECONDS   Request timeout in seconds (default: 30)
  --max-size BYTES    Maximum HTML size in bytes (default: 2000000)
  --help              Show help message
  --version           Show version information
```

## Output Structure

Captured articles are saved with the following structure:

```
/path/to/Vault/
├── 2024-01/
│   ├── how-to-learn-python-programming.md    # Title-based filename
│   ├── react-hooks-complete-guide.md        # Human-readable
│   └── machine-learning-basics-1.md         # Collision resolution
├── 2024-02/
│   └── web-articles/                         # Subfolder (if configured)
│       ├── understanding-docker-containers.md
│       └── javascript-best-practices.md
└── ...
```

### Generated Markdown Format

```markdown
---
title: Example Article Title
source: https://example.com/how-to-learn-python-programming
retrieved_at: 2024-01-15T10:30:00Z
published_at: 2024-01-10T08:00:00Z
author: Jane Doe
description: Article description extracted from meta tags
keywords: python, programming, tutorial
tags:
  - "#web"                    # From config file
  - "#archived"               # From config file
  - "#python"                 # From SEO keywords
  - "#programming"            # From SEO keywords  
  - "#tutorial"               # From SEO keywords
selector: article
---

# Example Article Title

Article content converted from HTML to Markdown format...
```

## Error Codes

The tool uses specific exit codes for different error conditions:

- `0`: Success
- `1`: General error (invalid arguments, file system errors)
- `2`: No selector matched sufficient content
- `3`: Network timeout
- `4`: Content size exceeds limit
- `5`: Text encoding error
- `6`: HTTP fetch error
- `7`: Conversion error
- `8`: File write error
- `9`: Configuration error

## Examples

### Basic Usage with Tags
```bash
# Capture web article with custom tags
obsidian-capture https://blog.com/python-tutorial \
  --vault ~/ObsidianVault \
  --tags "tutorial,beginner,python"

# Capture local HTML file with tags
obsidian-capture ~/Downloads/premium-article.html \
  --vault ~/ObsidianVault \
  --tags "premium,research,important"

# With config file and additional CLI tags  
obsidian-capture https://news.com/tech-article \
  --config ~/.obsidian-capture.yml \
  --tags "breaking-news,technology"
```

### Local File Processing
```bash
# Process paywall content saved as HTML
obsidian-capture ~/Downloads/nytimes-article.html \
  --vault ~/ObsidianVault \
  --subfolder "premium-articles" \
  --tags "paywall,journalism"

# Batch process local HTML files
for file in ~/Downloads/articles/*.html; do
  obsidian-capture "$file" \
    --vault ~/ObsidianVault \
    --subfolder "batch-$(date +%Y%m%d)" \
    --tags "batch-processed"
done

# Preview local file before processing
obsidian-capture ./saved-article.html --dry --format json
```

### JSON Output
```bash
obsidian-capture https://example.com/article --vault /vault --format json
```

```json
{
  "success": true,
  "url": "https://example.com/article",
  "output_path": "/vault/2024-01/example-article.md",
  "title": "Example Article",
  "author": "Jane Doe",
  "word_count": 500,
  "reading_time": 3,
  "selector_used": "article",
  "file_size": 2567
}
```

### Batch Processing
```bash
# Process multiple URLs
for url in https://blog.example.com/post1 https://news.example.com/article2; do
  obsidian-capture "$url" --vault /vault --subfolder "batch-$(date +%Y%m%d)"
done
```

### Integration with Scripts
```bash
#!/bin/bash
# Capture article (URL or local file) and handle errors
if obsidian-capture "$1" --vault "$OBSIDIAN_VAULT" --format json > result.json; then
  echo "Successfully captured: $(jq -r '.title' result.json)"
else
  case $? in
    2) echo "Error: No content found with configured selectors" ;;
    3) echo "Error: Network timeout" ;;
    4) echo "Error: Content too large" ;;
    *) echo "Error: Capture failed" ;;
  esac
fi

# Process all HTML files in a directory
#!/bin/bash
for html_file in ~/Downloads/articles/*.html; do
  if [[ -f "$html_file" ]]; then
    echo "Processing: $(basename "$html_file")"
    obsidian-capture "$html_file" \
      --vault ~/ObsidianVault \
      --subfolder "imported-$(date +%Y%m)" \
      --tags "imported,local-file"
  fi
done
```

## Development

### Requirements
- Python 3.8+
- Dependencies: `requests`, `beautifulsoup4`, `html2text`, `PyYAML`, `python-slugify`, `python-dateutil`
- Dev dependencies: `pytest`, `vcrpy`, `ruff`, `mypy`

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests

# Run with coverage
pytest --cov=src/obsidian_capture
```

### Code Quality
```bash
# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type checking (if mypy installed)
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.