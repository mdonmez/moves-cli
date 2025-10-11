import pytest
from unittest.mock import patch
import pymupdf
from moves_cli.core.components import section_producer
from moves_cli.data.models import Section


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temporary directory for test PDFs"""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def transcript_pdf(temp_pdf_dir):
    """Create a simple transcript PDF for testing"""
    pdf_path = temp_pdf_dir / "transcript.pdf"

    # Create a simple PDF with text
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4 size # type: ignore

    # Add text to the page
    text = "This is a sample transcript. It contains multiple sentences. This is for testing PDF extraction."
    page.insert_text((50, 50), text, fontsize=12)

    doc.save(pdf_path)
    doc.close()

    return pdf_path


@pytest.fixture
def presentation_pdf(temp_pdf_dir):
    """Create a simple presentation PDF with multiple slides"""
    pdf_path = temp_pdf_dir / "presentation.pdf"

    doc = pymupdf.open()

    # Create 3 slides
    for i in range(3):
        page = doc.new_page(width=595, height=842)  # type: ignore
        text = f"Slide {i + 1} Title\n\nThis is the content of slide {i + 1}."
        page.insert_text((50, 50), text, fontsize=12)

    doc.save(pdf_path)
    doc.close()

    return pdf_path


@pytest.fixture
def empty_pdf(temp_pdf_dir):
    """Create an empty PDF (no text)"""
    pdf_path = temp_pdf_dir / "empty.pdf"

    doc = pymupdf.open()
    doc.new_page(width=595, height=842)  # Create page but don't add text # type: ignore

    doc.save(pdf_path)
    doc.close()

    return pdf_path


@pytest.fixture
def corrupt_pdf(temp_pdf_dir):
    """Create a corrupted PDF file"""
    pdf_path = temp_pdf_dir / "corrupt.pdf"

    # Write invalid PDF content
    pdf_path.write_text("This is not a valid PDF file", encoding="utf-8")

    return pdf_path


class TestExtractPDFTranscript:
    """Test PDF text extraction for transcripts"""

    def test_extract_transcript_basic(self, transcript_pdf):
        """Test basic transcript extraction"""
        result = section_producer._extract_pdf(transcript_pdf, "transcript")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "sample transcript" in result.lower()

    def test_extract_transcript_removes_extra_whitespace(self, transcript_pdf):
        """Test that extraction removes extra whitespace"""
        result = section_producer._extract_pdf(transcript_pdf, "transcript")

        # Should not have multiple consecutive spaces
        assert "  " not in result
        # Should not have newlines
        assert "\n" not in result

    def test_extract_transcript_joins_words_with_single_space(self, transcript_pdf):
        """Test that words are joined with single spaces"""
        result = section_producer._extract_pdf(transcript_pdf, "transcript")

        words = result.split()
        # Should have multiple words
        assert len(words) > 5
        # Words should be separated by single spaces when joined
        assert result == " ".join(words)

    def test_extract_transcript_preserves_text_content(self, transcript_pdf):
        """Test that text content is preserved"""
        result = section_producer._extract_pdf(transcript_pdf, "transcript")

        # Check that key words from the original text are present
        assert "sample" in result.lower()
        assert "transcript" in result.lower()
        assert "testing" in result.lower()

    def test_extract_empty_transcript(self, empty_pdf):
        """Test extracting from empty PDF"""
        result = section_producer._extract_pdf(empty_pdf, "transcript")

        # Should return empty string or whitespace
        assert result.strip() == ""

    def test_extract_transcript_multipage(self, temp_pdf_dir):
        """Test transcript extraction from multi-page PDF"""
        pdf_path = temp_pdf_dir / "multipage_transcript.pdf"

        doc = pymupdf.open()
        # Create 3 pages with different text
        for i in range(3):
            page = doc.new_page(width=595, height=842)  # type: ignore
            text = f"Page {i + 1} content with unique text."
            page.insert_text((50, 50), text, fontsize=12)

        doc.save(pdf_path)
        doc.close()

        result = section_producer._extract_pdf(pdf_path, "transcript")

        # Should contain text from all pages
        assert "Page 1" in result
        assert "Page 2" in result
        assert "Page 3" in result


class TestExtractPDFPresentation:
    """Test PDF text extraction for presentations with slide markers"""

    def test_extract_presentation_basic(self, presentation_pdf):
        """Test basic presentation extraction"""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_extract_presentation_has_slide_markers(self, presentation_pdf):
        """Test that presentation extraction includes slide markers"""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        # Should have markdown headers for slides
        assert "# Slide Page 0" in result
        assert "# Slide Page 1" in result
        assert "# Slide Page 2" in result

    def test_extract_presentation_slide_count(self, presentation_pdf):
        """Test that all slides are extracted"""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        # Count the number of slide markers
        slide_markers = result.count("# Slide Page")
        assert slide_markers == 3

    def test_extract_presentation_separates_slides(self, presentation_pdf):
        """Test that slides are separated by double newlines"""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        # Slides should be separated by \n\n
        slides = result.split("\n\n")
        assert len(slides) == 3

    def test_extract_presentation_preserves_slide_content(self, presentation_pdf):
        """Test that slide content is preserved"""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        # Check for content from each slide
        assert "Slide 1" in result
        assert "Slide 2" in result
        assert "Slide 3" in result

    def test_extract_presentation_removes_extra_whitespace_per_slide(
        self, presentation_pdf
    ):
        """Test that whitespace is normalized within each slide"""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        # Split into individual slides
        slides = result.split("\n\n")

        for slide in slides:
            # Within slide content (after the header), should not have multiple spaces
            lines = slide.split("\n")
            if len(lines) > 1:
                content = lines[1]  # Content after header
                # Should not have consecutive spaces
                assert "  " not in content

    def test_extract_empty_presentation(self, empty_pdf):
        """Test extracting from empty presentation PDF"""
        result = section_producer._extract_pdf(empty_pdf, "presentation")

        # Should still have slide marker even if empty
        assert "# Slide Page 0" in result

    def test_extract_presentation_single_slide(self, temp_pdf_dir):
        """Test presentation with single slide"""
        pdf_path = temp_pdf_dir / "single_slide.pdf"

        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)  # type: ignore
        text = "Single slide content"
        page.insert_text((50, 50), text, fontsize=12)

        doc.save(pdf_path)
        doc.close()

        result = section_producer._extract_pdf(pdf_path, "presentation")

        assert "# Slide Page 0" in result
        assert "Single slide" in result
        # Should have exactly one slide
        assert result.count("# Slide Page") == 1


class TestExtractPDFErrorHandling:
    """Test error handling for corrupt or invalid PDFs"""

    def test_extract_corrupt_pdf_raises_runtime_error(self, corrupt_pdf):
        """Test that corrupt PDF raises RuntimeError"""
        with pytest.raises(RuntimeError, match="PDF extraction failed"):
            section_producer._extract_pdf(corrupt_pdf, "transcript")

    def test_extract_nonexistent_pdf_raises_runtime_error(self, temp_pdf_dir):
        """Test that nonexistent PDF raises RuntimeError"""
        nonexistent = temp_pdf_dir / "nonexistent.pdf"

        with pytest.raises(RuntimeError, match="PDF extraction failed"):
            section_producer._extract_pdf(nonexistent, "transcript")

    def test_extract_corrupt_presentation_raises_runtime_error(self, corrupt_pdf):
        """Test that corrupt presentation PDF raises RuntimeError"""
        with pytest.raises(RuntimeError, match="PDF extraction failed"):
            section_producer._extract_pdf(corrupt_pdf, "presentation")

    def test_error_message_includes_file_path(self, corrupt_pdf):
        """Test that error message includes the file path"""
        try:
            section_producer._extract_pdf(corrupt_pdf, "transcript")
        except RuntimeError as e:
            assert str(corrupt_pdf) in str(e)

    def test_error_message_includes_extraction_type(self, corrupt_pdf):
        """Test that error message includes extraction type"""
        try:
            section_producer._extract_pdf(corrupt_pdf, "transcript")
        except RuntimeError as e:
            assert "transcript" in str(e)

    def test_error_wraps_original_exception(self, corrupt_pdf):
        """Test that RuntimeError wraps the original exception"""
        try:
            section_producer._extract_pdf(corrupt_pdf, "transcript")
        except RuntimeError as e:
            # Should have a cause (the original exception)
            assert e.__cause__ is not None


class TestConversionFunctions:
    """Test conversion between Section objects and dictionaries"""

    def test_convert_to_list(self):
        """Test converting Section objects to list of dicts"""
        sections = [
            Section(content="First section", section_index=0),
            Section(content="Second section", section_index=1),
        ]

        result = section_producer.convert_to_list(sections)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"content": "First section", "section_index": 0}
        assert result[1] == {"content": "Second section", "section_index": 1}

    def test_convert_to_list_empty(self):
        """Test converting empty list"""
        result = section_producer.convert_to_list([])

        assert result == []

    def test_convert_to_list_preserves_order(self):
        """Test that conversion preserves section order"""
        sections = [
            Section(content="Section 2", section_index=2),
            Section(content="Section 0", section_index=0),
            Section(content="Section 1", section_index=1),
        ]

        result = section_producer.convert_to_list(sections)

        assert result[0]["section_index"] == 2
        assert result[1]["section_index"] == 0
        assert result[2]["section_index"] == 1

    def test_convert_to_objects(self):
        """Test converting list of dicts to Section objects"""
        section_list = [
            {"content": "First section", "section_index": 0},
            {"content": "Second section", "section_index": 1},
        ]

        result = section_producer.convert_to_objects(section_list)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(s, Section) for s in result)
        assert result[0].content == "First section"
        assert result[0].section_index == 0
        assert result[1].content == "Second section"
        assert result[1].section_index == 1

    def test_convert_to_objects_empty(self):
        """Test converting empty list to objects"""
        result = section_producer.convert_to_objects([])

        assert result == []

    def test_convert_to_objects_preserves_order(self):
        """Test that object conversion preserves order"""
        section_list = [
            {"content": "Section 2", "section_index": 2},
            {"content": "Section 0", "section_index": 0},
        ]

        result = section_producer.convert_to_objects(section_list)

        assert result[0].section_index == 2
        assert result[1].section_index == 0

    def test_round_trip_conversion(self):
        """Test that converting to list and back preserves data"""
        original = [
            Section(content="First section", section_index=0),
            Section(content="Second section", section_index=1),
        ]

        # Convert to list and back
        as_list = section_producer.convert_to_list(original)
        result = section_producer.convert_to_objects(as_list)

        # Should be equivalent
        assert len(result) == len(original)
        for orig, res in zip(original, result):
            assert res.content == orig.content
            assert res.section_index == orig.section_index


class TestGenerateSectionsMocked:
    """Test generate_sections with mocked LLM calls"""

    def test_generate_sections_calls_extract_pdf(
        self, transcript_pdf, presentation_pdf
    ):
        """Test that generate_sections calls _extract_pdf for both files"""
        with (
            patch("moves_cli.core.components.section_producer._extract_pdf") as mock_extract,
            patch("moves_cli.core.components.section_producer._call_llm") as mock_llm,
        ):
            mock_extract.return_value = "extracted text"
            mock_llm.return_value = ["Section 1", "Section 2"]

            section_producer.generate_sections(
                presentation_pdf, transcript_pdf, "test-model", "test-key"
            )

            # Should call extract twice (once for presentation, once for transcript)
            assert mock_extract.call_count == 2

    def test_generate_sections_extracts_presentation_first(
        self, transcript_pdf, presentation_pdf
    ):
        """Test that presentation is extracted before transcript"""
        with (
            patch("moves_cli.core.components.section_producer._extract_pdf") as mock_extract,
            patch("moves_cli.core.components.section_producer._call_llm") as mock_llm,
        ):
            mock_extract.return_value = "extracted text"
            mock_llm.return_value = ["Section 1"]

            section_producer.generate_sections(
                presentation_pdf, transcript_pdf, "test-model", "test-key"
            )

            # First call should be for presentation
            first_call = mock_extract.call_args_list[0]
            assert first_call[0][0] == presentation_pdf
            assert first_call[0][1] == "presentation"

    def test_generate_sections_extracts_transcript_second(
        self, transcript_pdf, presentation_pdf
    ):
        """Test that transcript is extracted after presentation"""
        with (
            patch("moves_cli.core.components.section_producer._extract_pdf") as mock_extract,
            patch("moves_cli.core.components.section_producer._call_llm") as mock_llm,
        ):
            mock_extract.return_value = "extracted text"
            mock_llm.return_value = ["Section 1"]

            section_producer.generate_sections(
                presentation_pdf, transcript_pdf, "test-model", "test-key"
            )

            # Second call should be for transcript
            second_call = mock_extract.call_args_list[1]
            assert second_call[0][0] == transcript_pdf
            assert second_call[0][1] == "transcript"

    def test_generate_sections_returns_section_objects(
        self, transcript_pdf, presentation_pdf
    ):
        """Test that generate_sections returns Section objects"""
        with (
            patch("moves_cli.core.components.section_producer._extract_pdf") as mock_extract,
            patch("moves_cli.core.components.section_producer._call_llm") as mock_llm,
        ):
            mock_extract.return_value = "extracted text"
            mock_llm.return_value = ["Section 1", "Section 2", "Section 3"]

            result = section_producer.generate_sections(
                presentation_pdf, transcript_pdf, "test-model", "test-key"
            )

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(s, Section) for s in result)

    def test_generate_sections_sets_correct_indices(
        self, transcript_pdf, presentation_pdf
    ):
        """Test that sections have correct indices"""
        with (
            patch("moves_cli.core.components.section_producer._extract_pdf") as mock_extract,
            patch("moves_cli.core.components.section_producer._call_llm") as mock_llm,
        ):
            mock_extract.return_value = "extracted text"
            mock_llm.return_value = ["Section 1", "Section 2", "Section 3"]

            result = section_producer.generate_sections(
                presentation_pdf, transcript_pdf, "test-model", "test-key"
            )

            # Indices should be 0, 1, 2
            assert result[0].section_index == 0
            assert result[1].section_index == 1
            assert result[2].section_index == 2

    def test_generate_sections_uses_llm_content(self, transcript_pdf, presentation_pdf):
        """Test that sections use content from LLM"""
        with (
            patch("moves_cli.core.components.section_producer._extract_pdf") as mock_extract,
            patch("moves_cli.core.components.section_producer._call_llm") as mock_llm,
        ):
            mock_extract.return_value = "extracted text"
            mock_llm.return_value = ["LLM content 1", "LLM content 2"]

            result = section_producer.generate_sections(
                presentation_pdf, transcript_pdf, "test-model", "test-key"
            )

            assert result[0].content == "LLM content 1"
            assert result[1].content == "LLM content 2"


class TestPDFExtractionIntegration:
    """Integration tests for PDF extraction with real files"""

    def test_extract_and_compare_types(self, transcript_pdf, presentation_pdf):
        """Test that transcript and presentation extractions differ"""
        transcript_result = section_producer._extract_pdf(transcript_pdf, "transcript")
        presentation_result = section_producer._extract_pdf(
            presentation_pdf, "presentation"
        )

        # Transcript should not have slide markers
        assert "# Slide Page" not in transcript_result

        # Presentation should have slide markers
        assert "# Slide Page" in presentation_result

    def test_extract_complex_presentation(self, temp_pdf_dir):
        """Test extracting presentation with varied content"""
        pdf_path = temp_pdf_dir / "complex_presentation.pdf"

        doc = pymupdf.open()

        # Create slides with different types of content
        for i in range(5):
            page = doc.new_page(width=595, height=842)  # type: ignore
            text = f"Slide {i + 1}\nBullet point 1\nBullet point 2\nConclusion text"
            page.insert_text((50, 50), text, fontsize=12)

        doc.save(pdf_path)
        doc.close()

        result = section_producer._extract_pdf(pdf_path, "presentation")

        # Should have 5 slides
        assert result.count("# Slide Page") == 5

        # Should contain content from all slides
        for i in range(5):
            assert f"Slide {i + 1}" in result

    def test_extract_transcript_with_special_characters(self, temp_pdf_dir):
        """Test transcript extraction with special characters"""
        pdf_path = temp_pdf_dir / "special_chars.pdf"

        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)  # type: ignore

        # Add text with special characters
        text = (
            'Testing special chars: quotes "text", dashes - em—dash, and apostrophe\'s'
        )
        page.insert_text((50, 50), text, fontsize=12)

        doc.save(pdf_path)
        doc.close()

        result = section_producer._extract_pdf(pdf_path, "transcript")

        # Should contain the text
        assert "special" in result.lower()
        assert "quotes" in result.lower()

