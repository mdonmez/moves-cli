"""Consolidated tests for component modules."""

import pytest
from unittest.mock import patch
import pymupdf
from moves_cli.core.components import chunk_producer, section_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.data.models import Section, Chunk, SimilarityResult


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_sections():
    """Create sample sections for testing."""
    return [
        Section(content="This is section zero with some content", section_index=0),
        Section(content="This is section one with more content", section_index=1),
        Section(content="This is section two with different words", section_index=2),
    ]


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        Chunk(
            partial_content="hello world",
            source_sections=[Section(content="hello world", section_index=0)],
        ),
        Chunk(
            partial_content="goodbye earth",
            source_sections=[Section(content="goodbye earth", section_index=1)],
        ),
    ]


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temporary directory for test PDFs."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def transcript_pdf(temp_pdf_dir):
    """Create a simple transcript PDF for testing."""
    pdf_path = temp_pdf_dir / "transcript.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # type: ignore
    page.insert_text((50, 50), "This is a sample transcript for testing.", fontsize=12)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def presentation_pdf(temp_pdf_dir):
    """Create a presentation PDF with multiple slides."""
    pdf_path = temp_pdf_dir / "presentation.pdf"
    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)  # type: ignore
        page.insert_text((50, 50), f"Slide {i + 1} content", fontsize=12)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


# ============================================================================
# Chunk Producer Tests
# ============================================================================


class TestChunkProducer:
    """Critical tests for chunk production."""

    def test_generate_chunks_basic(self, sample_sections):
        """Test basic chunk generation."""
        window_size = 5
        chunks = chunk_producer.generate_chunks(sample_sections, window_size)

        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)

    def test_chunks_have_correct_window_size(self, sample_sections):
        """Test chunks have correct word count."""
        window_size = 5
        chunks = chunk_producer.generate_chunks(sample_sections, window_size)

        for chunk in chunks:
            assert len(chunk.partial_content.split()) == window_size

    def test_chunks_are_normalized(self, sample_sections):
        """Test chunk content is normalized."""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=5)

        for chunk in chunks:
            assert chunk.partial_content.islower()
            assert "  " not in chunk.partial_content

    def test_chunks_span_sections(self):
        """Test chunks can span multiple sections."""
        sections = [
            Section(content="First section words", section_index=0),
            Section(content="Second section words", section_index=1),
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)

        multi_section_chunks = [c for c in chunks if len(c.source_sections) > 1]
        assert len(multi_section_chunks) > 0

    def test_insufficient_words_returns_empty(self):
        """Test returns empty list when insufficient words."""
        sections = [Section(content="only three words", section_index=0)]
        chunks = chunk_producer.generate_chunks(sections, window_size=10)

        assert chunks == []

    def test_default_window_size(self, sample_sections):
        """Test default window size of 8."""
        chunks = chunk_producer.generate_chunks(sample_sections)

        for chunk in chunks:
            assert len(chunk.partial_content.split()) == 8


# ============================================================================
# Section Producer Tests
# ============================================================================


class TestSectionProducer:
    """Critical tests for section production from PDFs."""

    def test_extract_transcript_basic(self, transcript_pdf):
        """Test basic transcript extraction."""
        result = section_producer._extract_pdf(transcript_pdf, "transcript")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "sample transcript" in result.lower()

    def test_extract_transcript_whitespace_handling(self, transcript_pdf):
        """Test whitespace normalization."""
        result = section_producer._extract_pdf(transcript_pdf, "transcript")

        assert "  " not in result  # No double spaces
        assert "\n" not in result  # No newlines

    def test_extract_presentation_basic(self, presentation_pdf):
        """Test basic presentation extraction."""
        result = section_producer._extract_pdf(presentation_pdf, "presentation")

        assert isinstance(result, str)
        assert "slide" in result.lower()


# ============================================================================
# Similarity Calculator Tests
# ============================================================================


class TestSimilarityCalculator:
    """Critical tests for similarity calculation."""

    def test_default_weights(self):
        """Test default weights (60% semantic, 40% phonetic)."""
        calculator = SimilarityCalculator()

        assert calculator.semantic_weight == 0.6
        assert calculator.phonetic_weight == 0.4
        assert calculator.semantic_weight + calculator.phonetic_weight == 1.0

    def test_custom_weights(self):
        """Test custom weight configuration."""
        calculator = SimilarityCalculator(semantic_weight=0.7, phonetic_weight=0.3)

        assert calculator.semantic_weight == 0.7
        assert calculator.phonetic_weight == 0.3

    def test_compare_basic(self, sample_chunks):
        """Test basic similarity comparison."""
        calculator = SimilarityCalculator()

        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.8),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.6),
            ]

            results = calculator.compare("test input", [sample_chunks[0]])

            assert len(results) > 0
            mock_semantic.assert_called_once()
            mock_phonetic.assert_called_once()

    def test_extreme_weights(self, sample_chunks):
        """Test with extreme weight configurations."""
        # 100% semantic
        calc1 = SimilarityCalculator(semantic_weight=1.0, phonetic_weight=0.0)
        assert calc1.semantic_weight == 1.0

        # 100% phonetic
        calc2 = SimilarityCalculator(semantic_weight=0.0, phonetic_weight=1.0)
        assert calc2.phonetic_weight == 1.0
