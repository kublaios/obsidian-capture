# Obsidian Capture Development Instructions

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Project Overview

Obsidian Capture is a Python command-line tool that captures HTML content from URLs or local files and converts them to Markdown files for Obsidian vaults. The tool supports intelligent content extraction, metadata preservation, and automatic organization.

## Working Effectively

### Bootstrap and Install Dependencies
```bash
# Install the project in development mode (takes ~7 seconds)
pip install -e .

# Install development dependencies individually (due to potential network timeouts)
pip install pytest ruff
# Note: "pip install -e .[dev]" may fail due to network timeouts - install dev deps individually instead
```

### Build and Test
- **NEVER CANCEL**: All build and test operations complete quickly (under 10 seconds)
- **Tests**: `pytest tests/` - takes 1.3 seconds, runs 310 tests. NEVER CANCEL - very fast.
- **Linting**: `ruff check src tests` - takes 0.02 seconds. NEVER CANCEL - very fast.
- **Format check**: `ruff format --check src tests` - takes 0.02 seconds. NEVER CANCEL - very fast.
- **Format code**: `ruff format src tests` - takes 0.02 seconds to format all files.

### Command Timing Expectations
- **Install**: `pip install -e .` takes ~7 seconds
- **Test**: `pytest tests/` takes ~1.3 seconds for 310 tests
- **Lint**: `ruff check src tests` takes ~0.02 seconds  
- **Format**: `ruff format --check src tests` takes ~0.02 seconds
- **Capture**: Processing articles takes ~0.2 seconds per file
- **Acceptance test**: `python3 acceptance_test.py` takes ~1 second

## Testing and Validation

### Acceptance Tests
```bash
# Run comprehensive acceptance tests (takes ~1 second)
python3 acceptance_test.py
```

### Unit Tests
```bash
# Run all tests - 310 tests pass in 1.3 seconds. NEVER CANCEL.
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage (if pytest-cov installed)
pytest --cov=src/obsidian_capture tests/
```

### Manual Validation Scenarios
Always test these scenarios after making changes:

#### Scenario 1: Local HTML File Processing
```bash
# Create test file (with sufficient content for extraction)
echo '<html><head><title>Test Article</title></head><body><article><h1>Test Article Title</h1><p>This is a comprehensive test article with substantial content for testing the obsidian-capture tool. It contains multiple paragraphs to ensure it meets the minimum character requirements for content extraction.</p><p>Content with <strong>bold</strong> text and <em>italic</em> text. This article has enough content to pass the minimum character threshold of 80 characters that is required by the tool.</p><p>Additional paragraph to make sure we have plenty of content for testing all the functionality including metadata extraction, content conversion, and file creation.</p></article></body></html>' > /tmp/test.html

# Create test vault
mkdir -p /tmp/test-vault

# Test dry run (preview without writing)
python3 -m obsidian_capture.cli /tmp/test.html --vault /tmp/test-vault --dry

# Test actual capture with tags
python3 -m obsidian_capture.cli /tmp/test.html --vault /tmp/test-vault --tags "test,local" --format json

# Verify output file was created
ls -la /tmp/test-vault/
cat /tmp/test-vault/*/test-article.md
```

#### Scenario 2: Configuration File Testing
```bash
# Copy and modify sample config
cp config.sample.yml /tmp/test-config.yml
sed -i 's|~/Documents/MyVault|/tmp/test-vault|' /tmp/test-config.yml

# Test with configuration
python3 -m obsidian_capture.cli /tmp/test.html --config /tmp/test-config.yml --tags "config-test"
```

#### Scenario 3: CLI Commands Validation
```bash
# Test help command
python3 -m obsidian_capture.cli --help

# Test version command  
python3 -m obsidian_capture.cli --version

# Test CLI with various options
python3 -m obsidian_capture.cli /tmp/test.html --vault /tmp/test-vault --subfolder "articles" --dry --format json
```

## Code Quality

### Pre-commit Validation
Always run before committing:
```bash
# Check code style and correctness (~0.02 seconds)
ruff check src tests

# Check formatting (~0.02 seconds)
ruff format --check src tests

# Run tests (~1.3 seconds for 310 tests)
pytest tests/

# Run acceptance tests (~1 second)
python3 acceptance_test.py
```

### Fix Common Issues
```bash
# Auto-fix style issues
ruff check --fix src tests

# Auto-format code
ruff format src tests
```

## Project Structure

### Key Directories
- `src/obsidian_capture/` - Main source code
  - `cli.py` - Command-line interface
  - `capture.py` - Main capture orchestration
  - `fetch.py` - HTML fetching (URLs and local files)
  - `extract.py` - Content extraction with CSS selectors
  - `convert.py` - HTML to Markdown conversion
  - `metadata.py` - Metadata extraction and processing
  - `naming.py` - File naming and path resolution
  - `config.py` - Configuration management
- `tests/` - Test suite (310 tests)
  - `unit/` - Unit tests
  - `integration/` - Integration tests
- `scripts/` - Development scripts
- `templates/` - Template files

### Important Files
- `pyproject.toml` - Project configuration and dependencies
- `config.sample.yml` - Sample configuration file
- `acceptance_test.py` - Comprehensive acceptance test
- `.github/workflows/test.yml` - CI/CD pipeline

## Common Tasks

### Adding New Features
1. Create unit tests first in `tests/unit/`
2. Implement feature in appropriate module in `src/obsidian_capture/`
3. Add integration tests if needed in `tests/integration/`
4. Update CLI interface in `cli.py` if needed
5. Run validation: `ruff check src tests && pytest tests/`
6. Test manually with scenarios above

### Debugging Issues
1. Run acceptance tests: `python3 acceptance_test.py`
2. Run specific test category: `pytest tests/unit/test_specific.py -v`
3. Test CLI manually with dry run: `python3 -m obsidian_capture.cli <input> --dry`
4. Check error codes (see README.md for exit code meanings)

### Performance Considerations
- Content extraction is very fast (~0.2 seconds per article)
- Test suite is comprehensive and fast (310 tests in 1.3 seconds)
- Linting is immediate (~0.02 seconds)
- Network fetching respects timeout settings (default 30 seconds)

## Network and Environment Limitations

### Network Access
- **Local HTML files**: Always work and should be tested
- **Network URLs**: May not work in restricted environments (firewalls, no internet)
- **Fallback testing**: Always use local HTML files for development testing

### Dependencies
- **Core dependencies**: Usually install successfully (requests, beautifulsoup4, html2text, etc.)
- **Dev dependencies**: May timeout during install - install individually with `pip install pytest ruff`
- **Python version**: Requires Python 3.8+, works with Python 3.12

## Configuration

### Sample Configuration Usage
```yaml
vault: "/path/to/vault"
selectors:
  - "article"
  - "main"
  - "body"
tags:
  - "web"
  - "archived"
exclusion_selectors:
  - "footer"
  - ".advertisement"
```

### CLI Usage Examples
```bash
# Basic local file capture
obsidian-capture /path/to/file.html --vault ~/vault

# With configuration file
obsidian-capture /path/to/file.html --config config.yml

# Minimal command using default config (~/.obsidian-capture.yml)
# Uses vault path defined in config file, no optional arguments needed
obsidian-capture /path/to/file.html

# Remote URL capture (may not work in restricted network environments)
# Include for completeness - prefer local HTML files for development testing
obsidian-capture https://example.com/article --vault ~/vault --timeout 30

# Dry run preview
obsidian-capture /path/to/file.html --vault ~/vault --dry

# JSON output
obsidian-capture /path/to/file.html --vault ~/vault --format json
```

## Troubleshooting

### Installation Issues
- If `pip install -e .[dev]` fails with timeouts, install dev dependencies individually
- Check Python version with `python3 --version` (requires 3.8+)

### Test Failures
- All 310 tests should pass - if any fail, investigate the specific failure
- Run `python3 acceptance_test.py` for quick validation
- Check that dependencies are properly installed

### Performance Issues
- Normal processing time is ~0.2 seconds per article
- If slower, check for large HTML files or complex CSS selectors
- Tests should complete in under 2 seconds total

Always validate changes by running the complete test suite and manual scenarios before committing.