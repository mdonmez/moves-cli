import pytest
import json
from pathlib import Path
from moves_cli.core.speaker_manager import SpeakerManager
from moves_cli.utils import data_handler


@pytest.fixture
def mock_data_folder(tmp_path, monkeypatch):
    """Replace DATA_FOLDER with a temporary directory for testing"""
    monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)
    return tmp_path


@pytest.fixture
def speaker_manager(mock_data_folder):
    """Create a SpeakerManager instance with mocked data folder"""
    return SpeakerManager()


@pytest.fixture
def sample_presentation(tmp_path):
    """Create a sample presentation file"""
    presentation_path = tmp_path / "presentation.pdf"
    presentation_path.write_text("Sample presentation content")
    return presentation_path


@pytest.fixture
def sample_transcript(tmp_path):
    """Create a sample transcript file"""
    transcript_path = tmp_path / "transcript.pdf"
    transcript_path.write_text("Sample transcript content")
    return transcript_path


@pytest.fixture
def alternative_presentation(tmp_path):
    """Create an alternative presentation file for testing edits"""
    presentation_path = tmp_path / "new_presentation.pdf"
    presentation_path.write_text("New presentation content")
    return presentation_path


@pytest.fixture
def alternative_transcript(tmp_path):
    """Create an alternative transcript file for testing edits"""
    transcript_path = tmp_path / "new_transcript.pdf"
    transcript_path.write_text("New transcript content")
    return transcript_path


class TestSpeakerManagerAdd:
    """Test adding speakers to the system"""

    def test_add_creates_speaker_with_valid_files(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test that adding a speaker with valid files creates the speaker successfully"""
        name = "John Doe"

        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        assert speaker.name == name
        assert speaker.speaker_id.startswith("john-doe-")
        assert speaker.source_presentation == sample_presentation.resolve()
        assert speaker.source_transcript == sample_transcript.resolve()

        # Verify speaker.json was created
        speaker_folder = mock_data_folder / "speakers" / speaker.speaker_id
        speaker_json = speaker_folder / "speaker.json"
        assert speaker_json.exists()

        # Verify content of speaker.json
        data = json.loads(speaker_json.read_text())
        assert data["name"] == name
        assert data["speaker_id"] == speaker.speaker_id
        assert data["source_presentation"] == str(sample_presentation.resolve())
        assert data["source_transcript"] == str(sample_transcript.resolve())

    def test_add_with_duplicate_name_fails(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that adding a speaker with a name matching an existing speaker ID fails"""
        # Add first speaker
        speaker1 = speaker_manager.add(
            "First Speaker", sample_presentation, sample_transcript
        )

        # Try to add speaker with name equal to the first speaker's ID
        with pytest.raises(
            ValueError,
            match=f"Given name '{speaker1.speaker_id}' can't be a same with one of the existing speakers' IDs",
        ):
            speaker_manager.add(
                speaker1.speaker_id, sample_presentation, sample_transcript
            )

    def test_add_multiple_speakers_with_same_name_allowed(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that adding multiple speakers with same name is allowed (different IDs)"""
        name = "John Doe"

        speaker1 = speaker_manager.add(name, sample_presentation, sample_transcript)
        speaker2 = speaker_manager.add(name, sample_presentation, sample_transcript)

        # Should have different IDs due to random suffix
        assert speaker1.speaker_id != speaker2.speaker_id
        assert speaker1.name == speaker2.name

    def test_add_resolves_paths(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that add resolves relative paths to absolute paths"""
        name = "Test Speaker"

        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        # Paths should be resolved (absolute)
        assert speaker.source_presentation.is_absolute()
        assert speaker.source_transcript.is_absolute()

    def test_add_creates_speakers_directory(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test that add creates the speakers directory if it doesn't exist"""
        speakers_path = mock_data_folder / "speakers"
        assert not speakers_path.exists()

        speaker_manager.add("Test Speaker", sample_presentation, sample_transcript)

        assert speakers_path.exists()

    def test_add_handles_special_characters_in_name(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that add handles special characters in speaker names"""
        name = "María García-López Jr."

        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        assert speaker.name == name
        # ID should be URL-safe
        assert all(c.isalnum() or c in "-_" for c in speaker.speaker_id)


class TestSpeakerManagerEdit:
    """Test editing speaker information"""

    def test_edit_presentation_path(
        self,
        speaker_manager,
        sample_presentation,
        sample_transcript,
        alternative_presentation,
        mock_data_folder,
    ):
        """Test editing a speaker's presentation path"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )
        original_transcript = speaker.source_transcript

        updated_speaker = speaker_manager.edit(
            speaker, source_presentation=alternative_presentation
        )

        assert updated_speaker.source_presentation == alternative_presentation.resolve()
        assert updated_speaker.source_transcript == original_transcript

        # Verify updated data in speaker.json
        speaker_json = (
            mock_data_folder / "speakers" / speaker.speaker_id / "speaker.json"
        )
        data = json.loads(speaker_json.read_text())
        assert data["source_presentation"] == str(alternative_presentation.resolve())

    def test_edit_transcript_path(
        self,
        speaker_manager,
        sample_presentation,
        sample_transcript,
        alternative_transcript,
        mock_data_folder,
    ):
        """Test editing a speaker's transcript path"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )
        original_presentation = speaker.source_presentation

        updated_speaker = speaker_manager.edit(
            speaker, source_transcript=alternative_transcript
        )

        assert updated_speaker.source_transcript == alternative_transcript.resolve()
        assert updated_speaker.source_presentation == original_presentation

        # Verify updated data in speaker.json
        speaker_json = (
            mock_data_folder / "speakers" / speaker.speaker_id / "speaker.json"
        )
        data = json.loads(speaker_json.read_text())
        assert data["source_transcript"] == str(alternative_transcript.resolve())

    def test_edit_both_paths(
        self,
        speaker_manager,
        sample_presentation,
        sample_transcript,
        alternative_presentation,
        alternative_transcript,
        mock_data_folder,
    ):
        """Test editing both presentation and transcript paths"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )

        updated_speaker = speaker_manager.edit(
            speaker,
            source_presentation=alternative_presentation,
            source_transcript=alternative_transcript,
        )

        assert updated_speaker.source_presentation == alternative_presentation.resolve()
        assert updated_speaker.source_transcript == alternative_transcript.resolve()

        # Verify updated data in speaker.json
        speaker_json = (
            mock_data_folder / "speakers" / speaker.speaker_id / "speaker.json"
        )
        data = json.loads(speaker_json.read_text())
        assert data["source_presentation"] == str(alternative_presentation.resolve())
        assert data["source_transcript"] == str(alternative_transcript.resolve())

    def test_edit_with_no_changes(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test editing a speaker without providing any new values"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )
        original_presentation = speaker.source_presentation
        original_transcript = speaker.source_transcript

        updated_speaker = speaker_manager.edit(speaker)

        assert updated_speaker.source_presentation == original_presentation
        assert updated_speaker.source_transcript == original_transcript

    def test_edit_resolves_paths(
        self,
        speaker_manager,
        sample_presentation,
        sample_transcript,
        alternative_presentation,
    ):
        """Test that edit resolves relative paths to absolute paths"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )

        updated_speaker = speaker_manager.edit(
            speaker, source_presentation=alternative_presentation
        )

        # Path should be resolved (absolute)
        assert updated_speaker.source_presentation.is_absolute()

    def test_edit_updates_speaker_object(
        self,
        speaker_manager,
        sample_presentation,
        sample_transcript,
        alternative_presentation,
    ):
        """Test that edit updates the speaker object directly"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )

        speaker_manager.edit(speaker, source_presentation=alternative_presentation)

        # The speaker object should be updated in place
        assert speaker.source_presentation == alternative_presentation.resolve()


class TestSpeakerManagerResolve:
    """Test resolving speakers by ID or name"""

    def test_resolve_by_exact_id(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test resolving a speaker by their exact ID"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )

        resolved = speaker_manager.resolve(speaker.speaker_id)

        assert resolved.speaker_id == speaker.speaker_id
        assert resolved.name == speaker.name
        assert resolved.source_presentation == speaker.source_presentation
        assert resolved.source_transcript == speaker.source_transcript

    def test_resolve_by_name(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test resolving a speaker by their name"""
        name = "John Doe"
        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        resolved = speaker_manager.resolve(name)

        assert resolved.speaker_id == speaker.speaker_id
        assert resolved.name == name

    def test_resolve_prefers_id_over_name(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that resolve prefers matching by ID over name"""
        # Create two speakers with same name
        name = "John Doe"
        speaker1 = speaker_manager.add(name, sample_presentation, sample_transcript)
        _ = speaker_manager.add(name, sample_presentation, sample_transcript)

        # Resolve using speaker1's ID should return speaker1, not speaker2
        resolved = speaker_manager.resolve(speaker1.speaker_id)

        assert resolved.speaker_id == speaker1.speaker_id

    def test_resolve_error_multiple_speakers_with_same_name(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test error handling when multiple speakers have the same name"""
        name = "John Doe"
        _ = speaker_manager.add(name, sample_presentation, sample_transcript)
        _ = speaker_manager.add(name, sample_presentation, sample_transcript)

        with pytest.raises(
            ValueError, match=f"Multiple speakers found matching '{name}'"
        ):
            speaker_manager.resolve(name)

    def test_resolve_error_speaker_not_found(self, speaker_manager):
        """Test error handling when no speaker matches the pattern"""
        with pytest.raises(ValueError, match="No speaker found matching 'nonexistent'"):
            speaker_manager.resolve("nonexistent")

    def test_resolve_error_message_includes_all_matches(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that error message for multiple matches lists all matching speakers"""
        name = "John Doe"
        speaker1 = speaker_manager.add(name, sample_presentation, sample_transcript)
        speaker2 = speaker_manager.add(name, sample_presentation, sample_transcript)

        try:
            speaker_manager.resolve(name)
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            error_msg = str(e)
            assert speaker1.speaker_id in error_msg
            assert speaker2.speaker_id in error_msg
            assert name in error_msg

    def test_resolve_with_single_speaker_by_name_succeeds(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that resolving by name succeeds when only one speaker has that name"""
        name = "Unique Name"
        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        resolved = speaker_manager.resolve(name)

        assert resolved.speaker_id == speaker.speaker_id

    def test_resolve_is_case_sensitive(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that resolve is case-sensitive for names"""
        _ = speaker_manager.add("John Doe", sample_presentation, sample_transcript)

        # Should not find with different case
        with pytest.raises(ValueError, match="No speaker found matching 'john doe'"):
            speaker_manager.resolve("john doe")


class TestSpeakerManagerList:
    """Test listing all speakers"""

    def test_list_returns_empty_for_no_speakers(self, speaker_manager):
        """Test that list returns empty list when no speakers exist"""
        speakers = speaker_manager.list()

        assert speakers == []

    def test_list_returns_all_speakers(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that list returns all added speakers"""
        speaker1 = speaker_manager.add(
            "Speaker One", sample_presentation, sample_transcript
        )
        speaker2 = speaker_manager.add(
            "Speaker Two", sample_presentation, sample_transcript
        )
        speaker3 = speaker_manager.add(
            "Speaker Three", sample_presentation, sample_transcript
        )

        speakers = speaker_manager.list()

        assert len(speakers) == 3
        speaker_ids = [s.speaker_id for s in speakers]
        assert speaker1.speaker_id in speaker_ids
        assert speaker2.speaker_id in speaker_ids
        assert speaker3.speaker_id in speaker_ids

    def test_list_returns_speaker_with_correct_attributes(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that list returns speakers with all correct attributes"""
        name = "Test Speaker"
        added_speaker = speaker_manager.add(
            name, sample_presentation, sample_transcript
        )

        speakers = speaker_manager.list()
        speaker = speakers[0]

        assert speaker.name == name
        assert speaker.speaker_id == added_speaker.speaker_id
        assert speaker.source_presentation == sample_presentation.resolve()
        assert speaker.source_transcript == sample_transcript.resolve()

    def test_list_ignores_non_speaker_folders(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test that list ignores folders without speaker.json"""
        speaker_manager.add("Valid Speaker", sample_presentation, sample_transcript)

        # Create a folder without speaker.json
        invalid_folder = mock_data_folder / "speakers" / "invalid-folder"
        invalid_folder.mkdir(parents=True)

        speakers = speaker_manager.list()

        assert len(speakers) == 1

    def test_list_ignores_files_in_speakers_directory(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test that list ignores files in speakers directory"""
        speaker_manager.add("Valid Speaker", sample_presentation, sample_transcript)

        # Create a file in speakers directory
        (mock_data_folder / "speakers" / "random_file.txt").write_text("content")

        speakers = speaker_manager.list()

        assert len(speakers) == 1

    def test_list_converts_path_strings_to_path_objects(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that list converts path strings back to Path objects"""
        speaker_manager.add("Test Speaker", sample_presentation, sample_transcript)

        speakers = speaker_manager.list()
        speaker = speakers[0]

        assert isinstance(speaker.source_presentation, Path)
        assert isinstance(speaker.source_transcript, Path)


class TestSpeakerManagerDelete:
    """Test deleting speakers"""

    def test_delete_removes_speaker(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test that delete removes a speaker and their folder"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )
        speaker_path = mock_data_folder / "speakers" / speaker.speaker_id

        result = speaker_manager.delete(speaker)

        assert result is True
        assert not speaker_path.exists()

    def test_delete_removes_speaker_from_list(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that deleted speaker no longer appears in list"""
        speaker1 = speaker_manager.add(
            "Speaker One", sample_presentation, sample_transcript
        )
        speaker2 = speaker_manager.add(
            "Speaker Two", sample_presentation, sample_transcript
        )

        speaker_manager.delete(speaker1)
        speakers = speaker_manager.list()

        assert len(speakers) == 1
        assert speakers[0].speaker_id == speaker2.speaker_id

    def test_delete_removes_all_speaker_data(
        self, speaker_manager, sample_presentation, sample_transcript, mock_data_folder
    ):
        """Test that delete removes all files in speaker folder"""
        speaker = speaker_manager.add(
            "Test Speaker", sample_presentation, sample_transcript
        )
        speaker_path = mock_data_folder / "speakers" / speaker.speaker_id

        # Add some additional files
        (speaker_path / "extra_file.txt").write_text("extra content")
        (speaker_path / "sections.json").write_text('{"sections": []}')

        result = speaker_manager.delete(speaker)

        assert result is True
        assert not speaker_path.exists()

    def test_delete_multiple_speakers(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test deleting multiple speakers"""
        speaker1 = speaker_manager.add(
            "Speaker One", sample_presentation, sample_transcript
        )
        speaker2 = speaker_manager.add(
            "Speaker Two", sample_presentation, sample_transcript
        )
        speaker3 = speaker_manager.add(
            "Speaker Three", sample_presentation, sample_transcript
        )

        speaker_manager.delete(speaker1)
        speaker_manager.delete(speaker3)

        speakers = speaker_manager.list()
        assert len(speakers) == 1
        assert speakers[0].speaker_id == speaker2.speaker_id


class TestSpeakerManagerIntegration:
    """Integration tests for complete workflows"""

    def test_add_edit_resolve_workflow(
        self,
        speaker_manager,
        sample_presentation,
        sample_transcript,
        alternative_presentation,
    ):
        """Test complete workflow: add, edit, and resolve speaker"""
        # Add speaker
        name = "John Doe"
        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        # Edit speaker
        speaker_manager.edit(speaker, source_presentation=alternative_presentation)

        # Resolve by name
        resolved = speaker_manager.resolve(name)
        assert resolved.source_presentation == alternative_presentation.resolve()

        # Resolve by ID
        resolved_by_id = speaker_manager.resolve(speaker.speaker_id)
        assert resolved_by_id.speaker_id == speaker.speaker_id

    def test_add_multiple_list_delete_workflow(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test workflow with multiple speakers: add, list, delete"""
        # Add multiple speakers
        speaker1 = speaker_manager.add("Alice", sample_presentation, sample_transcript)
        speaker2 = speaker_manager.add("Bob", sample_presentation, sample_transcript)
        speaker3 = speaker_manager.add(
            "Charlie", sample_presentation, sample_transcript
        )

        # List all
        speakers = speaker_manager.list()
        assert len(speakers) == 3

        # Delete one
        speaker_manager.delete(speaker2)

        # List again
        speakers = speaker_manager.list()
        assert len(speakers) == 2
        speaker_ids = [s.speaker_id for s in speakers]
        assert speaker1.speaker_id in speaker_ids
        assert speaker3.speaker_id in speaker_ids
        assert speaker2.speaker_id not in speaker_ids

    def test_speaker_persistence(
        self, speaker_manager, sample_presentation, sample_transcript
    ):
        """Test that speaker data persists across SpeakerManager instances"""
        # Add speaker with first instance
        name = "Persistent Speaker"
        speaker = speaker_manager.add(name, sample_presentation, sample_transcript)

        # Create new instance
        new_manager = SpeakerManager()

        # Should be able to retrieve speaker
        speakers = new_manager.list()
        assert len(speakers) == 1
        assert speakers[0].speaker_id == speaker.speaker_id

        resolved = new_manager.resolve(name)
        assert resolved.speaker_id == speaker.speaker_id
