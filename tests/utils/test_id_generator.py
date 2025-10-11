import re
from moves_cli.utils import id_generator


class TestSpeakerID:
    """Tests for speaker ID generation."""

    def test_format_validation_simple_name(self):
        input_name = "John Doe"
        expected_start = "john-doe"

        speaker_id = id_generator.generate_speaker_id(input_name)

        assert speaker_id.startswith(expected_start + "-")
        assert len(speaker_id.split("-")[-1]) == 5

    def test_format_validation_accented_name(self):
        input_name = "María García"
        expected_start = "maria-garcia"

        speaker_id = id_generator.generate_speaker_id(input_name)

        assert speaker_id.startswith(expected_start + "-")
        assert len(speaker_id.split("-")[-1]) == 5

    def test_format_validation_special_characters(self):
        input_name = "Dr. Smith Jr."
        expected_start = "dr-smith-jr"

        speaker_id = id_generator.generate_speaker_id(input_name)

        assert speaker_id.startswith(expected_start + "-")
        assert len(speaker_id.split("-")[-1]) == 5

    def test_url_safety_simple_name(self):
        input_name = "John Doe"

        speaker_id = id_generator.generate_speaker_id(input_name)

        assert re.match(r"^[a-zA-Z0-9_-]+$", speaker_id)

    def test_url_safety_special_characters(self):
        input_name = "María García!@#"

        speaker_id = id_generator.generate_speaker_id(input_name)

        assert re.match(r"^[a-zA-Z0-9_-]+$", speaker_id)

    def test_url_safety_mixed_special_characters(self):
        input_name = "Name with special chars!?"

        speaker_id = id_generator.generate_speaker_id(input_name)

        assert re.match(r"^[a-zA-Z0-9_-]+$", speaker_id)


class TestSuffixGeneration:
    """Tests for ID suffix generation."""

    def test_5_character_suffix(self):
        input_name = "Test Name"

        speaker_id = id_generator.generate_speaker_id(input_name)
        suffix = speaker_id.split("-")[-1]

        assert len(suffix) == 5
        assert suffix.isalnum()


class TestHistoryID:
    """Tests for history ID generation."""

    def test_format_validation(self):
        history_id = id_generator.generate_history_id()

        assert re.match(r"^\d{8}_\d{2}-\d{2}-\d{2}$", history_id)
