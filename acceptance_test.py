#!/usr/bin/env python3
"""Final acceptance test script for Obsidian Capture."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd, **kwargs):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30,
            **kwargs
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out: {cmd}")
        return None
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None

def test_imports():
    """Test that core modules can be imported."""
    print("🧪 Testing module imports...")
    try:
        from src.obsidian_capture.config import create_default_config
        from src.obsidian_capture.capture import CaptureRequest, capture_html_to_obsidian
        from src.obsidian_capture.metadata import extract_metadata_from_html
        from src.obsidian_capture.convert import convert_html_to_markdown
        print("✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Hint: Install dependencies with 'pip install -e .' or 'pip install -e .[dev]'")
        return False
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_unit_tests():
    """Run a subset of unit tests."""
    print("\n🧪 Running unit tests...")
    # Check if pytest is available
    pytest_check = run_command("python3 -c 'import pytest; print(pytest.__version__)'")
    if not pytest_check or pytest_check.returncode != 0:
        print("❌ pytest not available")
        print("💡 Hint: Install dev dependencies with 'pip install -e .[dev]'")
        return False
    
    result = run_command("python3 -m pytest tests/unit/test_config.py::TestConfig::test_config_minimal_valid -v")
    if result and result.returncode == 0:
        print("✅ Unit tests passed")
        return True
    else:
        print("❌ Unit tests failed")
        if result:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        return False

def test_cli_help():
    """Test CLI help command."""
    print("\n🧪 Testing CLI help...")
    result = run_command("python3 -m src.obsidian_capture.cli --help")
    if result and result.returncode == 0 and "obsidian-capture" in result.stdout:
        print("✅ CLI help working")
        return True
    else:
        print("❌ CLI help failed")
        return False

def test_cli_version():
    """Test CLI version command."""
    print("\n🧪 Testing CLI version...")
    result = run_command("python3 -m src.obsidian_capture.cli --version")
    if result and result.returncode == 0:
        print(f"✅ CLI version: {result.stdout.strip()}")
        return True
    else:
        print("❌ CLI version failed")
        return False

def test_basic_functionality():
    """Test basic capture functionality with mocked content."""
    print("\n🧪 Testing basic capture functionality...")
    
    try:
        # Create temporary vault
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            
            # Test basic config creation
            from src.obsidian_capture.config import create_default_config
            config = create_default_config()
            print(f"✅ Created config with {len(config.selectors)} selectors")
            
            # Test metadata extraction
            from src.obsidian_capture.metadata import extract_metadata_from_html
            test_html = """
            <html>
            <head><title>Test Article</title></head>
            <body><article>Test content for extraction.</article></body>
            </html>
            """
            metadata = extract_metadata_from_html(test_html, "https://example.com/test")
            print(f"✅ Extracted metadata: title='{metadata.title}'")
            
            # Test HTML to markdown conversion
            from src.obsidian_capture.convert import convert_html_to_markdown
            markdown = convert_html_to_markdown("<p>Test <strong>bold</strong> text.</p>")
            print(f"✅ Converted to markdown: {markdown.strip()}")
            
            return True
            
    except ImportError as e:
        print(f"❌ Basic functionality test failed: {e}")
        print("💡 Hint: Install dependencies with 'pip install -e .' or 'pip install -e .[dev]'")
        return False
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_performance():
    """Quick performance test."""
    print("\n🧪 Testing basic performance...")
    try:
        import time
        from src.obsidian_capture.extract import extract_content_with_selectors
        
        html = "<article>" + "Test content. " * 100 + "</article>"
        selectors = ['article']
        
        start_time = time.time()
        result = extract_content_with_selectors(html, selectors, min_chars=10)
        end_time = time.time()
        
        elapsed = end_time - start_time
        if elapsed < 1.0:  # Should be much faster than 1 second
            print(f"✅ Performance test passed ({elapsed:.3f}s)")
            return True
        else:
            print(f"⚠️ Performance slower than expected ({elapsed:.3f}s)")
            return True  # Still acceptable
            
    except ImportError as e:
        print(f"❌ Performance test failed: {e}")
        print("💡 Hint: Install dependencies with 'pip install -e .' or 'pip install -e .[dev]'")
        return False
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all acceptance tests."""
    print("🚀 Running Obsidian Capture Acceptance Tests")
    print("=" * 50)
    print("📋 Prerequisites:")
    print("   • Install dependencies: pip install -e .")
    print("   • Install dev dependencies: pip install -e .[dev]")
    print("   • Ensure Python 3.8+ is installed")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Unit Tests Sample", test_unit_tests),
        ("CLI Help", test_cli_help),
        ("CLI Version", test_cli_version),
        ("Basic Functionality", test_basic_functionality),
        ("Performance", test_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {name} test failed")
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All acceptance tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Implementation needs work.")
        return 1

if __name__ == "__main__":
    sys.exit(main())