import pytest
from pathlib import Path
from moves_cli.utils import data_handler


@pytest.fixture
def mock_data_folder(tmp_path, monkeypatch):
    """Replace DATA_FOLDER with a temporary directory for testing"""
    monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)
    return tmp_path


class TestWriteRead:
    """Test writing and reading text files"""

    def test_write_creates_file(self, mock_data_folder):
        """Test that write creates a new file with correct content"""
        test_path = Path("test_file.txt")
        test_data = "Hello, World!"

        result = data_handler.write(test_path, test_data)

        assert result is True
        assert (mock_data_folder / test_path).exists()
        assert (mock_data_folder / test_path).read_text(encoding="utf-8") == test_data

    def test_write_overwrites_existing_file(self, mock_data_folder):
        """Test that write overwrites existing file content"""
        test_path = Path("test_file.txt")
        initial_data = "Initial content"
        new_data = "New content"

        data_handler.write(test_path, initial_data)
        data_handler.write(test_path, new_data)

        assert (mock_data_folder / test_path).read_text(encoding="utf-8") == new_data

    def test_read_returns_correct_content(self, mock_data_folder):
        """Test that read returns the correct file content"""
        test_path = Path("test_file.txt")
        test_data = "Test content"

        data_handler.write(test_path, test_data)
        result = data_handler.read(test_path)

        assert result == test_data

    def test_write_read_with_unicode(self, mock_data_folder):
        """Test that write and read handle unicode characters correctly"""
        test_path = Path("unicode_file.txt")
        test_data = "Hello 世界 café ñoño 🎉"

        data_handler.write(test_path, test_data)
        result = data_handler.read(test_path)

        assert result == test_data

    def test_write_read_with_multiline(self, mock_data_folder):
        """Test that write and read handle multiline text correctly"""
        test_path = Path("multiline.txt")
        test_data = "Line 1\nLine 2\nLine 3\n"

        data_handler.write(test_path, test_data)
        result = data_handler.read(test_path)

        assert result == test_data


class TestDirectoryCreation:
    """Test that directories are created automatically when needed"""

    def test_write_creates_parent_directories(self, mock_data_folder):
        """Test that write creates nested directories automatically"""
        test_path = Path("level1/level2/level3/test_file.txt")
        test_data = "Nested content"

        result = data_handler.write(test_path, test_data)

        assert result is True
        assert (mock_data_folder / test_path).exists()
        assert (mock_data_folder / test_path).read_text(encoding="utf-8") == test_data

    def test_write_handles_existing_directories(self, mock_data_folder):
        """Test that write works when parent directories already exist"""
        test_dir = mock_data_folder / "existing_dir"
        test_dir.mkdir()
        test_path = Path("existing_dir/test_file.txt")
        test_data = "Test content"

        result = data_handler.write(test_path, test_data)

        assert result is True
        assert (mock_data_folder / test_path).exists()


class TestErrorHandling:
    """Test error handling for missing files and invalid paths"""

    def test_read_raises_file_not_found(self, mock_data_folder):
        """Test that read raises FileNotFoundError for missing files"""
        test_path = Path("nonexistent_file.txt")

        with pytest.raises(FileNotFoundError, match="File not found"):
            data_handler.read(test_path)

    def test_read_raises_error_for_directory(self, mock_data_folder):
        """Test that read raises IsADirectoryError when path is a directory"""
        test_dir = Path("test_directory")
        (mock_data_folder / test_dir).mkdir()

        with pytest.raises(IsADirectoryError, match="Path is a directory"):
            data_handler.read(test_dir)

    def test_write_raises_runtime_error_on_failure(self, mock_data_folder, monkeypatch):
        """Test that write raises RuntimeError when write operation fails"""
        test_path = Path("test_file.txt")

        # Mock write_text to raise an exception
        def mock_write_text(*args, **kwargs):
            raise OSError("Disk full")

        # Create the parent directory first
        (mock_data_folder / test_path).parent.mkdir(parents=True, exist_ok=True)

        # Patch Path.write_text
        monkeypatch.setattr(Path, "write_text", mock_write_text)

        with pytest.raises(RuntimeError, match="Write operation failed"):
            data_handler.write(test_path, "data")

    def test_read_raises_runtime_error_on_failure(self, mock_data_folder, monkeypatch):
        """Test that read raises RuntimeError when read operation fails"""
        test_path = Path("test_file.txt")

        # Create the file first
        data_handler.write(test_path, "data")

        # Mock read_text to raise an exception
        def mock_read_text(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        with pytest.raises(RuntimeError, match="Read operation failed"):
            data_handler.read(test_path)


class TestListOperation:
    """Test listing directory contents"""

    def test_list_returns_empty_for_nonexistent_directory(self, mock_data_folder):
        """Test that list returns empty list for nonexistent directory"""
        result = data_handler.list(Path("nonexistent_dir"))

        assert result == []

    def test_list_returns_directory_contents(self, mock_data_folder):
        """Test that list returns all files and directories in a path"""
        test_dir = Path("test_dir")
        (mock_data_folder / test_dir).mkdir()
        (mock_data_folder / test_dir / "file1.txt").write_text("content1")
        (mock_data_folder / test_dir / "file2.txt").write_text("content2")
        (mock_data_folder / test_dir / "subdir").mkdir()

        result = data_handler.list(test_dir)

        assert len(result) == 3
        result_names = [p.name for p in result]
        assert "file1.txt" in result_names
        assert "file2.txt" in result_names
        assert "subdir" in result_names

    def test_list_returns_sorted_results(self, mock_data_folder):
        """Test that list returns items in sorted order"""
        test_dir = Path("test_dir")
        (mock_data_folder / test_dir).mkdir()
        (mock_data_folder / test_dir / "zebra.txt").write_text("z")
        (mock_data_folder / test_dir / "apple.txt").write_text("a")
        (mock_data_folder / test_dir / "middle.txt").write_text("m")

        result = data_handler.list(test_dir)

        result_names = [p.name for p in result]
        assert result_names == sorted(result_names)

    def test_list_raises_runtime_error_on_failure(self, mock_data_folder, monkeypatch):
        """Test that list raises RuntimeError when iteration fails"""
        test_dir = Path("test_dir")
        (mock_data_folder / test_dir).mkdir()

        # Mock iterdir to raise an exception
        def mock_iterdir(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "iterdir", mock_iterdir)

        with pytest.raises(RuntimeError, match="List operation failed"):
            data_handler.list(test_dir)


class TestDeleteOperation:
    """Test deleting files and directories"""

    def test_delete_removes_file(self, mock_data_folder):
        """Test that delete removes a file"""
        test_path = Path("test_file.txt")
        data_handler.write(test_path, "content")

        result = data_handler.delete(test_path)

        assert result is True
        assert not (mock_data_folder / test_path).exists()

    def test_delete_removes_directory(self, mock_data_folder):
        """Test that delete removes a directory and its contents"""
        test_dir = Path("test_dir")
        (mock_data_folder / test_dir).mkdir()
        (mock_data_folder / test_dir / "file.txt").write_text("content")
        (mock_data_folder / test_dir / "subdir").mkdir()

        result = data_handler.delete(test_dir)

        assert result is True
        assert not (mock_data_folder / test_dir).exists()

    def test_delete_raises_file_not_found(self, mock_data_folder):
        """Test that delete raises FileNotFoundError for nonexistent path"""
        test_path = Path("nonexistent_file.txt")

        with pytest.raises(FileNotFoundError, match="Path not found"):
            data_handler.delete(test_path)

    def test_delete_raises_runtime_error_on_failure(
        self, mock_data_folder, monkeypatch
    ):
        """Test that delete raises RuntimeError when delete operation fails"""
        test_path = Path("test_file.txt")
        data_handler.write(test_path, "content")

        # Mock unlink to raise an exception
        def mock_unlink(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        with pytest.raises(RuntimeError, match="Delete operation failed"):
            data_handler.delete(test_path)

    def test_delete_handles_special_file_types(self, mock_data_folder):
        """Test that delete handles non-standard file types (else branch)"""
        test_path = Path("special_file")
        # Create a file directly in the mock folder
        (mock_data_folder / test_path).touch()

        # Mock is_file and is_dir to return False to trigger else branch
        import unittest.mock

        with unittest.mock.patch.object(Path, "is_file", return_value=False):
            with unittest.mock.patch.object(Path, "is_dir", return_value=False):
                result = data_handler.delete(test_path)
                assert result is True


class TestRenameOperation:
    """Test renaming files"""

    def test_rename_changes_filename(self, mock_data_folder):
        """Test that rename changes the file name"""
        old_path = Path("old_name.txt")
        new_name = "new_name.txt"
        test_data = "Test content"

        data_handler.write(old_path, test_data)
        result = data_handler.rename(old_path, new_name)

        assert result == Path(new_name)
        assert not (mock_data_folder / old_path).exists()
        assert (mock_data_folder / new_name).exists()
        assert (mock_data_folder / new_name).read_text(encoding="utf-8") == test_data

    def test_rename_overwrites_existing_file(self, mock_data_folder):
        """Test that rename overwrites target file if it exists"""
        old_path = Path("old_name.txt")
        new_name = "new_name.txt"
        old_data = "Old content"
        existing_data = "Existing content"

        data_handler.write(old_path, old_data)
        data_handler.write(Path(new_name), existing_data)

        result = data_handler.rename(old_path, new_name)

        assert result == Path(new_name)
        assert (mock_data_folder / new_name).read_text(encoding="utf-8") == old_data

    def test_rename_raises_runtime_error_on_failure(
        self, mock_data_folder, monkeypatch
    ):
        """Test that rename raises RuntimeError when rename operation fails"""
        old_path = Path("old_name.txt")
        new_name = "new_name.txt"
        data_handler.write(old_path, "content")

        # Mock shutil.move to raise an exception
        import shutil

        def mock_move(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(shutil, "move", mock_move)

        with pytest.raises(RuntimeError, match="Rename operation failed"):
            data_handler.rename(old_path, new_name)


class TestCopyOperation:
    """Test copying files and directories"""

    def test_copy_file_to_directory(self, mock_data_folder):
        """Test that copy copies a file to a target directory"""
        source = Path("source_file.txt")
        target = Path("target_dir")
        test_data = "Test content"

        data_handler.write(source, test_data)
        result = data_handler.copy(source, target)

        assert result is True
        assert (mock_data_folder / source).exists()  # Original still exists
        assert (mock_data_folder / target / "source_file.txt").exists()
        content = (mock_data_folder / target / "source_file.txt").read_text(
            encoding="utf-8"
        )
        assert content == test_data

    def test_copy_directory_recursively(self, mock_data_folder):
        """Test that copy copies a directory and all its contents"""
        source = Path("source_dir")
        target = Path("target_dir")

        (mock_data_folder / source).mkdir()
        (mock_data_folder / source / "file1.txt").write_text("content1")
        (mock_data_folder / source / "subdir").mkdir()
        (mock_data_folder / source / "subdir" / "file2.txt").write_text("content2")

        result = data_handler.copy(source, target)

        assert result is True
        assert (mock_data_folder / target / "file1.txt").exists()
        assert (mock_data_folder / target / "subdir" / "file2.txt").exists()
        assert (mock_data_folder / target / "file1.txt").read_text(
            encoding="utf-8"
        ) == "content1"
        assert (mock_data_folder / target / "subdir" / "file2.txt").read_text(
            encoding="utf-8"
        ) == "content2"

    def test_copy_raises_file_not_found(self, mock_data_folder):
        """Test that copy raises FileNotFoundError for nonexistent source"""
        source = Path("nonexistent_file.txt")
        target = Path("target_dir")

        with pytest.raises(FileNotFoundError, match="Source not found"):
            data_handler.copy(source, target)

    def test_copy_creates_target_directory(self, mock_data_folder):
        """Test that copy creates target directory if it doesn't exist"""
        source = Path("source_file.txt")
        target = Path("nested/target/dir")
        test_data = "Test content"

        data_handler.write(source, test_data)
        result = data_handler.copy(source, target)

        assert result is True
        assert (mock_data_folder / target / "source_file.txt").exists()

    def test_copy_raises_runtime_error_when_target_creation_fails(
        self, mock_data_folder, monkeypatch
    ):
        """Test that copy raises RuntimeError when target directory creation fails"""
        source = Path("source_file.txt")
        target = Path("target_dir")
        data_handler.write(source, "content")

        # Mock mkdir to raise an exception
        original_mkdir = Path.mkdir

        def mock_mkdir(self, *args, **kwargs):
            # Only raise for the target path, not for source creation
            if "target_dir" in str(self):
                raise OSError("Permission denied")
            return original_mkdir(self, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", mock_mkdir)

        with pytest.raises(RuntimeError, match="Failed to create target directory"):
            data_handler.copy(source, target)

    def test_copy_raises_runtime_error_for_invalid_source_type(self, mock_data_folder):
        """Test that copy raises RuntimeError for source that is neither file nor directory"""
        source = Path("special_file")
        target = Path("target_dir")

        # Create a file but mock it to appear as neither file nor directory
        data_handler.write(source, "content")

        import unittest.mock

        with unittest.mock.patch.object(Path, "is_file", return_value=False):
            with unittest.mock.patch.object(Path, "is_dir", return_value=False):
                with pytest.raises(
                    RuntimeError, match="Source path is neither file nor directory"
                ):
                    data_handler.copy(source, target)

    def test_copy_raises_runtime_error_on_copy_failure(
        self, mock_data_folder, monkeypatch
    ):
        """Test that copy raises RuntimeError when copy operation fails"""
        source = Path("source_file.txt")
        target = Path("target_dir")
        data_handler.write(source, "content")

        # Mock shutil.copy2 to raise an exception
        import shutil

        def mock_copy2(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr(shutil, "copy2", mock_copy2)

        with pytest.raises(RuntimeError, match="Copy operation failed"):
            data_handler.copy(source, target)
