"""Unit tests for filename collision logic."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from src.obsidian_capture.naming import (
    NamingError,
    clean_directory_name,
    create_date_directory,
    create_full_directory_path,
    generate_filename,
    generate_full_path,
    resolve_final_path,
    validate_vault_path,
)


class TestGenerateFilename:
    """Test filename generation."""

    def test_title_to_filename(self):
        """Test filename generation from title."""
        filename = generate_filename("Hello World: A Test", "http://example.com")
        assert filename == "hello-world-a-test.md"

    def test_title_length_limiting(self):
        """Test filename length is limited."""
        long_title = "A" * 100
        filename = generate_filename(long_title, "http://example.com", max_length=20)
        # Should be "a" * 20 + ".md"
        assert len(filename) == 23  # 20 + 3 for ".md"
        assert filename.endswith(".md")

    def test_title_with_special_characters(self):
        """Test title with special characters is slugified."""
        filename = generate_filename("Hello & World!!! @#$", "http://example.com")
        assert filename == "hello-world.md"

    def test_title_with_unicode(self):
        """Test title with unicode characters."""
        filename = generate_filename("Héllo Wørld", "http://example.com")
        assert filename == "hello-world.md"

    def test_length_limiting_removes_trailing_hyphens(self):
        """Test length limiting removes trailing hyphens and underscores."""
        # Create a title that when slugified and truncated would end with hyphen
        title = "hello-world-test-very-long-title-that-exceeds"
        filename = generate_filename(title, "http://example.com", max_length=15)
        assert not filename.replace(".md", "").endswith("-")
        assert not filename.replace(".md", "").endswith("_")


class TestCreateDateDirectory:
    """Test date directory creation."""

    def test_create_date_directory_specific_date(self):
        """Test creating directory with specific date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            specific_date = datetime(2022, 5, 20)

            date_dir = create_date_directory(vault_path, specific_date)

            assert date_dir == vault_path / "2022-05"
            assert date_dir.exists()

    def test_create_date_directory_already_exists(self):
        """Test creating directory when it already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            specific_date = datetime(2023, 3, 10)

            # Create directory manually first
            existing_dir = vault_path / "2023-03"
            existing_dir.mkdir(parents=True)

            # Should not raise error
            date_dir = create_date_directory(vault_path, specific_date)
            assert date_dir == existing_dir

    def test_create_date_directory_permission_error(self):
        """Test error handling for permission issues."""
        # Use a path that would cause permission error
        invalid_path = Path("/root/nonexistent")

        with pytest.raises(NamingError, match="Failed to create date directory"):
            create_date_directory(invalid_path)


class TestCreateFullDirectoryPath:
    """Test full directory path creation."""

    def test_create_full_directory_no_subfolder(self):
        """Test creating full directory without subfolder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            specific_date = datetime(2023, 7, 15)

            full_dir = create_full_directory_path(vault_path, None, specific_date)

            assert full_dir == vault_path / "2023-07"
            assert full_dir.exists()

    def test_create_full_directory_with_subfolder(self):
        """Test creating full directory with subfolder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            specific_date = datetime(2023, 7, 15)

            full_dir = create_full_directory_path(vault_path, "articles", specific_date)

            assert full_dir == vault_path / "2023-07" / "articles"
            assert full_dir.exists()

    def test_create_full_directory_with_unsafe_subfolder(self):
        """Test creating full directory with unsafe subfolder name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            specific_date = datetime(2023, 7, 15)

            full_dir = create_full_directory_path(
                vault_path, "unsafe/\\name", specific_date
            )

            # Should clean the subfolder name
            expected_dir = vault_path / "2023-07" / "unsafename"
            assert full_dir == expected_dir
            assert full_dir.exists()


class TestCleanDirectoryName:
    """Test directory name cleaning."""

    def test_clean_normal_name(self):
        """Test cleaning normal directory name."""
        result = clean_directory_name("articles")
        assert result == "articles"

    def test_clean_unsafe_characters(self):
        """Test removing unsafe characters."""
        result = clean_directory_name('unsafe<>:"/\\|?*name')
        assert result == "unsafename"

    def test_clean_leading_trailing_dots_spaces(self):
        """Test removing leading/trailing dots and spaces."""
        result = clean_directory_name("  .folder.  ")
        assert result == "folder"

    def test_clean_long_name(self):
        """Test limiting name length."""
        long_name = "a" * 100
        result = clean_directory_name(long_name)
        assert len(result) == 50
        assert result == "a" * 50

    def test_clean_empty_name(self):
        """Test handling empty name."""
        result = clean_directory_name("")
        assert result == "misc"

    def test_clean_only_unsafe_characters(self):
        """Test name with only unsafe characters."""
        result = clean_directory_name('<>:"/\\|?*')
        assert result == "misc"

    def test_clean_only_dots_and_spaces(self):
        """Test name with only dots and spaces."""
        result = clean_directory_name("  . .. . ")
        assert result == "misc"


class TestResolveFinalPath:
    """Test final path resolution with collision handling."""

    def test_resolve_path_no_collision(self):
        """Test resolving path when no collision exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "test.md"

            result = resolve_final_path(directory, filename)
            assert result == directory / filename

    def test_resolve_path_with_collision(self):
        """Test resolving path with existing file collision."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "test.md"

            # Create existing file
            existing_file = directory / filename
            existing_file.touch()

            result = resolve_final_path(directory, filename)
            assert result == directory / "test-1.md"

    def test_resolve_path_multiple_collisions(self):
        """Test resolving path with multiple collisions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "test.md"

            # Create multiple existing files
            (directory / "test.md").touch()
            (directory / "test-1.md").touch()
            (directory / "test-2.md").touch()

            result = resolve_final_path(directory, filename)
            assert result == directory / "test-3.md"

    def test_resolve_path_with_overwrite(self):
        """Test resolving path with overwrite enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "test.md"

            # Create existing file
            existing_file = directory / filename
            existing_file.touch()

            result = resolve_final_path(directory, filename, overwrite=True)
            assert result == directory / filename

    def test_resolve_path_excessive_collisions(self):
        """Test error handling for excessive collisions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "test.md"

            # Mock exists to always return True to simulate excessive collisions
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(NamingError, match="Too many filename collisions"):
                    resolve_final_path(directory, filename)

    def test_resolve_path_complex_filename(self):
        """Test resolving path with complex filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "complex-article-title.md"

            # Create existing file
            (directory / filename).touch()

            result = resolve_final_path(directory, filename)
            assert result == directory / "complex-article-title-1.md"

    def test_resolve_path_filename_without_extension(self):
        """Test resolving path with filename without extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            filename = "test"

            # Create existing file
            (directory / filename).touch()

            result = resolve_final_path(directory, filename)
            assert result == directory / "test-1"


class TestGenerateFullPath:
    """Test complete path generation."""

    def test_generate_full_path_with_collision(self):
        """Test generating path with collision handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            specific_date = datetime(2023, 6, 10)

            # Pre-create the directory structure and existing file
            date_dir = vault_path / "2023-06"
            date_dir.mkdir(parents=True)
            existing_file = date_dir / "test-article.md"
            existing_file.touch()

            result = generate_full_path(
                vault_path=vault_path,
                title="Test Article",
                url="http://example.com/article",
                date=specific_date,
            )

            expected = vault_path / "2023-06" / "test-article-1.md"
            assert result == expected


class TestValidateVaultPath:
    """Test vault path validation."""

    def test_validate_valid_directory(self):
        """Test validation of valid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            assert validate_vault_path(vault_path) is True

    def test_validate_nonexistent_path(self):
        """Test validation of nonexistent path."""
        nonexistent_path = Path("/nonexistent/path")
        assert validate_vault_path(nonexistent_path) is False

    def test_validate_file_instead_of_directory(self):
        """Test validation when path points to file instead of directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "testfile"
            file_path.touch()
            assert validate_vault_path(file_path) is False

    def test_validate_permission_error(self):
        """Test validation when directory is not writable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)

            # Mock the touch operation to fail
            with patch.object(Path, "touch", side_effect=PermissionError()):
                assert validate_vault_path(vault_path) is False

    def test_validate_general_exception(self):
        """Test validation with general exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)

            # Mock exists to raise exception
            with patch.object(Path, "exists", side_effect=Exception("Test error")):
                assert validate_vault_path(vault_path) is False
