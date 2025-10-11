import pytest
import tomlkit
from moves_cli.core.settings_editor import SettingsEditor
from moves_cli.data.models import Settings
from moves_cli.utils import data_handler


@pytest.fixture
def mock_data_folder(tmp_path, monkeypatch):
    """Replace DATA_FOLDER with a temporary directory for testing"""
    monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)
    return tmp_path


@pytest.fixture
def temp_template(tmp_path, monkeypatch):
    """Create a temporary settings template for testing"""
    template_path = tmp_path / "settings_template.toml"
    template_content = """# Test template
model = "gemini/gemini-2.0-flash"
key = "None"
"""
    template_path.write_text(template_content, encoding="utf-8")
    monkeypatch.setattr(SettingsEditor, "template", template_path)
    return template_path


@pytest.fixture
def editor(mock_data_folder, temp_template, monkeypatch):
    """Create a SettingsEditor instance for testing"""
    # Need to update the class attribute before instantiating
    settings_path = mock_data_folder / "settings.toml"
    monkeypatch.setattr(SettingsEditor, "settings", settings_path)
    return SettingsEditor()


class TestSettingsEditorInitialization:
    """Test SettingsEditor initialization"""

    def test_initialization_creates_settings_file(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that settings file is created on initialization if missing"""
        settings_path = mock_data_folder / "settings.toml"

        # Ensure file doesn't exist before
        assert not settings_path.exists()

        # Update class attribute before instantiating
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # Initialize editor
        SettingsEditor()

        # File should now exist
        assert settings_path.exists()

    def test_initialization_loads_defaults_from_template(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that defaults are loaded from template on initialization"""
        settings_path = mock_data_folder / "settings.toml"
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        editor = SettingsEditor()
        settings = editor.list()

        assert settings.model == "gemini/gemini-2.0-flash"
        assert settings.key == "None"

    def test_initialization_preserves_existing_settings(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that existing settings are preserved during initialization"""
        settings_path = mock_data_folder / "settings.toml"

        # Create existing settings file
        existing_content = """model = "custom-model"
key = "custom-key"
"""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(existing_content, encoding="utf-8")

        # Update class attribute before instantiating
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # Initialize editor
        editor = SettingsEditor()
        settings = editor.list()

        # Custom values should be preserved
        assert settings.model == "custom-model"
        assert settings.key == "custom-key"

    def test_initialization_merges_template_with_user_settings(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that user settings override template defaults"""
        settings_path = mock_data_folder / "settings.toml"

        # Create partial user settings
        user_content = """model = "user-model"
"""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(user_content, encoding="utf-8")

        # Update class attribute before instantiating
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # Initialize editor
        editor = SettingsEditor()
        settings = editor.list()

        # User value for model, default for key
        assert settings.model == "user-model"
        assert settings.key == "None"

    def test_initialization_handles_corrupted_settings(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that initialization handles corrupted settings file gracefully"""
        settings_path = mock_data_folder / "settings.toml"

        # Create corrupted settings file
        corrupted_content = "invalid toml [[[content"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(corrupted_content, encoding="utf-8")

        # Update class attribute before instantiating
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # Should not raise exception, should use defaults
        editor = SettingsEditor()
        settings = editor.list()

        assert settings.model == "gemini/gemini-2.0-flash"
        assert settings.key == "None"


class TestSettingsEditorSet:
    """Test setting values in settings"""

    def test_set_valid_key_model(self, editor, mock_data_folder):
        """Test setting a valid key (model)"""
        result = editor.set("model", "gpt-4")

        assert result is True

        settings = editor.list()
        assert settings.model == "gpt-4"

    def test_set_valid_key_api_key(self, editor, mock_data_folder):
        """Test setting a valid key (key)"""
        result = editor.set("key", "test-api-key-123")

        assert result is True

        settings = editor.list()
        assert settings.key == "test-api-key-123"

    def test_set_invalid_key_returns_false(self, editor):
        """Test that invalid keys are rejected (returns False)"""
        result = editor.set("invalid_key", "some_value")

        assert result is False

    def test_set_blank_key_returns_false(self, editor):
        """Test that blank keys are rejected"""
        result = editor.set("", "some_value")

        assert result is False

    def test_set_persists_to_disk(self, editor, mock_data_folder):
        """Test that settings are persisted to disk"""
        editor.set("model", "claude-3")

        settings_path = mock_data_folder / "settings.toml"
        content = settings_path.read_text(encoding="utf-8")

        assert "claude-3" in content

    def test_set_multiple_keys(self, editor):
        """Test setting multiple keys"""
        editor.set("model", "gpt-4")
        editor.set("key", "my-api-key")

        settings = editor.list()
        assert settings.model == "gpt-4"
        assert settings.key == "my-api-key"

    def test_set_overwrites_previous_value(self, editor):
        """Test that setting a key overwrites previous value"""
        editor.set("model", "model-v1")
        editor.set("model", "model-v2")

        settings = editor.list()
        assert settings.model == "model-v2"

    def test_set_preserves_other_keys(self, editor):
        """Test that setting one key preserves other keys"""
        editor.set("model", "custom-model")
        original_key = editor.list().key

        editor.set("model", "another-model")

        settings = editor.list()
        assert settings.model == "another-model"
        assert settings.key == original_key


class TestSettingsEditorUnset:
    """Test unsetting keys in settings"""

    def test_unset_returns_to_default(self, editor, temp_template):
        """Test that unsetting a key returns it to default value"""
        # Set a custom value
        editor.set("model", "custom-model")
        assert editor.list().model == "custom-model"

        # Unset it
        result = editor.unset("model")

        assert result is True
        # Should return to default
        assert editor.list().model == "gemini/gemini-2.0-flash"

    def test_unset_valid_key(self, editor):
        """Test unsetting a valid key"""
        editor.set("key", "custom-key")
        result = editor.unset("key")

        assert result is True
        assert editor.list().key == "None"

    def test_unset_invalid_key_succeeds(self, editor):
        """Test that unsetting an invalid key doesn't fail"""
        result = editor.unset("nonexistent_key")

        # Should succeed (no-op)
        assert result is True

    def test_unset_persists_to_disk(self, editor, mock_data_folder):
        """Test that unsetting persists to disk"""
        editor.set("model", "custom-model")
        editor.unset("model")

        # Read from disk to verify
        settings_path = mock_data_folder / "settings.toml"
        content = tomlkit.parse(settings_path.read_text(encoding="utf-8"))

        assert content["model"] == "gemini/gemini-2.0-flash"

    def test_unset_after_set(self, editor):
        """Test unsetting after setting a value"""
        editor.set("model", "temp-model")
        editor.unset("model")

        settings = editor.list()
        assert settings.model == "gemini/gemini-2.0-flash"

    def test_unset_multiple_keys(self, editor):
        """Test unsetting multiple keys"""
        editor.set("model", "custom-model")
        editor.set("key", "custom-key")

        editor.unset("model")
        editor.unset("key")

        settings = editor.list()
        assert settings.model == "gemini/gemini-2.0-flash"
        assert settings.key == "None"

    def test_unset_preserves_other_keys(self, editor):
        """Test that unsetting one key preserves other keys"""
        editor.set("model", "custom-model")
        editor.set("key", "custom-key")

        editor.unset("model")

        settings = editor.list()
        assert settings.model == "gemini/gemini-2.0-flash"
        assert settings.key == "custom-key"

    def test_unset_save_error_raises_runtime_error(self, editor, monkeypatch):
        """Test that unset raises RuntimeError when save fails"""
        from unittest.mock import MagicMock

        # Mock _save to raise an exception
        mock_save = MagicMock(side_effect=IOError("Disk full"))
        monkeypatch.setattr(editor, "_save", mock_save)

        with pytest.raises(RuntimeError, match="Failed to unset key"):
            editor.unset("model")


class TestSettingsEditorPersistence:
    """Test settings persistence to disk"""

    def test_settings_persisted_across_instances(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that settings are persisted across different instances"""
        settings_path = mock_data_folder / "settings.toml"
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # First instance
        editor1 = SettingsEditor()
        editor1.set("model", "persistent-model")
        editor1.set("key", "persistent-key")

        # Second instance
        editor2 = SettingsEditor()
        settings = editor2.list()

        assert settings.model == "persistent-model"
        assert settings.key == "persistent-key"

    def test_settings_file_is_valid_toml(self, editor, mock_data_folder):
        """Test that settings file is valid TOML"""
        editor.set("model", "test-model")

        settings_path = mock_data_folder / "settings.toml"
        content = settings_path.read_text(encoding="utf-8")

        # Should parse without error
        parsed = tomlkit.parse(content)
        assert parsed["model"] == "test-model"

    def test_settings_file_preserves_comments(self, editor, mock_data_folder):
        """Test that settings file preserves template comments"""
        editor.set("model", "new-model")

        settings_path = mock_data_folder / "settings.toml"
        content = settings_path.read_text(encoding="utf-8")

        # Comments from template should be preserved
        assert "# Test template" in content

    def test_settings_directory_created_if_missing(
        self, tmp_path, temp_template, monkeypatch
    ):
        """Test that settings directory is created if missing"""
        # Set up a deep path
        deep_path = tmp_path / "level1" / "level2" / "level3"
        monkeypatch.setattr(data_handler, "DATA_FOLDER", deep_path)

        settings_path = deep_path / "settings.toml"
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # Should not raise exception
        SettingsEditor()

        assert settings_path.exists()


class TestSettingsEditorList:
    """Test listing settings"""

    def test_list_returns_settings_instance(self, editor):
        """Test that list returns a Settings instance"""
        settings = editor.list()

        assert isinstance(settings, Settings)

    def test_list_contains_all_keys(self, editor):
        """Test that list contains all expected keys"""
        settings = editor.list()

        assert hasattr(settings, "model")
        assert hasattr(settings, "key")

    def test_list_reflects_current_values(self, editor):
        """Test that list reflects current values"""
        editor.set("model", "current-model")
        editor.set("key", "current-key")

        settings = editor.list()

        assert settings.model == "current-model"
        assert settings.key == "current-key"

    def test_list_after_unset(self, editor):
        """Test that list reflects defaults after unset"""
        editor.set("model", "temp-model")
        editor.unset("model")

        settings = editor.list()
        assert settings.model == "gemini/gemini-2.0-flash"


class TestSettingsEditorErrorHandling:
    """Test error handling in settings editor"""

    def test_set_with_invalid_type(self, editor):
        """Test setting a value with invalid type still works (TOML handles it)"""
        # TOML can handle various types
        result = editor.set("model", 123)
        assert result is True

        settings = editor.list()
        # Will be converted to string or handled by TOML
        assert settings.model == 123

    def test_invalid_key_does_not_modify_settings(self, editor):
        """Test that invalid keys don't modify settings"""
        original = editor.list()

        editor.set("invalid_key", "value")

        current = editor.list()
        assert current.model == original.model
        assert current.key == original.key

    def test_readonly_settings_file(self, editor, mock_data_folder):
        """Test handling of readonly settings file"""
        import os

        settings_path = editor.settings

        # First, ensure the file exists by writing to it
        if not settings_path.exists():
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.touch()

        # Make file readonly on Windows
        if os.name == "nt":
            os.chmod(settings_path, 0o444)

            try:
                with pytest.raises(RuntimeError, match="Failed to save settings"):
                    editor.set("model", "new-model")
            finally:
                # Restore permissions for cleanup
                os.chmod(settings_path, 0o666)
        else:
            # Skip test on non-Windows platforms
            pytest.skip("Test is Windows-specific")


class TestSettingsEditorIntegration:
    """Test integration scenarios"""

    def test_complete_workflow(self, editor):
        """Test complete workflow: set, list, unset, list"""
        # Set values
        editor.set("model", "workflow-model")
        editor.set("key", "workflow-key")

        # List values
        after_set = editor.list()
        assert after_set.model == "workflow-model"
        assert after_set.key == "workflow-key"

        # Unset one value
        editor.unset("model")

        # List again
        after_unset = editor.list()
        assert after_unset.model == "gemini/gemini-2.0-flash"
        assert after_unset.key == "workflow-key"

    def test_multiple_editors_same_file(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test multiple editors accessing the same file"""
        settings_path = mock_data_folder / "settings.toml"
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        editor1 = SettingsEditor()
        editor1.set("model", "editor1-model")

        # Second editor should see the changes
        editor2 = SettingsEditor()
        settings = editor2.list()

        assert settings.model == "editor1-model"

    def test_settings_survive_editor_recreation(
        self, mock_data_folder, temp_template, monkeypatch
    ):
        """Test that settings survive editor recreation"""
        settings_path = mock_data_folder / "settings.toml"
        monkeypatch.setattr(SettingsEditor, "settings", settings_path)

        # Create and modify
        editor1 = SettingsEditor()
        editor1.set("model", "persistent-model")
        del editor1

        # Recreate and verify
        editor2 = SettingsEditor()
        settings = editor2.list()

        assert settings.model == "persistent-model"
