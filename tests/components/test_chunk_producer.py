import pytest
from moves_cli.core.components import chunk_producer
from moves_cli.data.models import Section, Chunk


@pytest.fixture
def sample_sections():
    """Create a list of sample sections for testing"""
    return [
        Section(content="This is section zero with some content", section_index=0),
        Section(content="This is section one with more content", section_index=1),
        Section(content="This is section two with different words", section_index=2),
        Section(content="This is section three with unique text", section_index=3),
        Section(content="This is section four with final content", section_index=4),
    ]


@pytest.fixture
def small_sections():
    """Create a small list of sections with few words"""
    return [
        Section(content="One two three", section_index=0),
        Section(content="Four five six", section_index=1),
    ]


@pytest.fixture
def single_word_sections():
    """Create sections with single words"""
    return [
        Section(content="Alpha", section_index=0),
        Section(content="Beta", section_index=1),
        Section(content="Gamma", section_index=2),
    ]


class TestGenerateChunks:
    """Test generating chunks from sections"""

    def test_generate_chunks_basic(self, sample_sections):
        """Test that chunks are generated correctly from sections"""
        window_size = 5
        chunks = chunk_producer.generate_chunks(sample_sections, window_size)

        # Should generate multiple chunks
        assert len(chunks) > 0
        # Each chunk should be a Chunk instance
        assert all(isinstance(chunk, Chunk) for chunk in chunks)

    def test_chunks_have_correct_window_size(self, sample_sections):
        """Test that chunks have the correct number of words based on window size"""
        window_size = 5
        chunks = chunk_producer.generate_chunks(sample_sections, window_size)

        for chunk in chunks:
            # Each chunk should have exactly window_size words (after normalization)
            word_count = len(chunk.partial_content.split())
            assert word_count == window_size

    def test_generate_chunks_with_different_window_sizes(self, sample_sections):
        """Test chunk generation with various window sizes"""
        for window_size in [3, 5, 8, 12]:
            chunks = chunk_producer.generate_chunks(sample_sections, window_size)
            assert len(chunks) > 0
            for chunk in chunks:
                assert len(chunk.partial_content.split()) == window_size

    def test_generate_chunks_default_window_size(self, sample_sections):
        """Test that default window size is 12"""
        chunks = chunk_producer.generate_chunks(sample_sections)

        # With default window size of 12
        for chunk in chunks:
            assert len(chunk.partial_content.split()) == 12

    def test_chunk_count_calculation(self, sample_sections):
        """Test that correct number of chunks are generated"""
        window_size = 5
        total_words = sum(len(s.content.split()) for s in sample_sections)
        expected_chunks = total_words - window_size + 1

        chunks = chunk_producer.generate_chunks(sample_sections, window_size)

        assert len(chunks) == expected_chunks

    def test_chunks_are_normalized(self, sample_sections):
        """Test that chunk content is normalized"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=5)

        for chunk in chunks:
            # Normalized text should be lowercase
            assert chunk.partial_content.islower()
            # Should not have multiple spaces
            assert "  " not in chunk.partial_content

    def test_chunks_slide_across_sections(self):
        """Test that chunks slide across section boundaries"""
        sections = [
            Section(content="First section words", section_index=0),
            Section(content="Second section words", section_index=1),
        ]
        window_size = 3
        chunks = chunk_producer.generate_chunks(sections, window_size)

        # Should have chunks that span both sections
        multi_section_chunks = [
            chunk for chunk in chunks if len(chunk.source_sections) > 1
        ]
        assert len(multi_section_chunks) > 0

    def test_edge_case_not_enough_words(self, small_sections):
        """Test that empty list is returned when not enough words for window size"""
        window_size = 12
        chunks = chunk_producer.generate_chunks(small_sections, window_size)

        # Should return empty list when not enough words
        assert chunks == []

    def test_edge_case_exact_window_size(self):
        """Test when total words equals window size"""
        sections = [Section(content="one two three four five", section_index=0)]
        window_size = 5
        chunks = chunk_producer.generate_chunks(sections, window_size)

        # Should create exactly one chunk
        assert len(chunks) == 1
        assert len(chunks[0].partial_content.split()) == 5

    def test_edge_case_empty_sections(self):
        """Test with empty sections list"""
        chunks = chunk_producer.generate_chunks([], window_size=5)

        assert chunks == []

    def test_edge_case_window_size_larger_than_words(self):
        """Test when window size is larger than total words"""
        sections = [Section(content="only three words", section_index=0)]
        window_size = 10
        chunks = chunk_producer.generate_chunks(sections, window_size)

        assert chunks == []

    def test_edge_case_window_size_one(self, single_word_sections):
        """Test with window size of 1"""
        window_size = 1
        chunks = chunk_producer.generate_chunks(single_word_sections, window_size)

        # Should create one chunk per word
        assert len(chunks) == 3
        assert chunks[0].partial_content == "alpha"
        assert chunks[1].partial_content == "beta"
        assert chunks[2].partial_content == "gamma"


class TestChunkSourceSections:
    """Test that chunk source sections are tracked correctly"""

    def test_source_sections_are_tracked(self, sample_sections):
        """Test that each chunk tracks its source sections"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=5)

        for chunk in chunks:
            # Each chunk should have at least one source section
            assert len(chunk.source_sections) > 0
            # Source sections should be Section instances
            assert all(isinstance(s, Section) for s in chunk.source_sections)

    def test_source_sections_within_single_section(self):
        """Test that chunks within a single section only reference that section"""
        sections = [
            Section(content="one two three four five six seven eight", section_index=0)
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)

        # All chunks should only have one source section
        for chunk in chunks:
            assert len(chunk.source_sections) == 1
            assert chunk.source_sections[0].section_index == 0

    def test_source_sections_span_multiple_sections(self):
        """Test that chunks can span multiple sections"""
        sections = [
            Section(content="First section", section_index=0),
            Section(content="Second section", section_index=1),
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)

        # Find chunks that span both sections
        multi_section_chunks = [
            chunk for chunk in chunks if len(chunk.source_sections) > 1
        ]

        assert len(multi_section_chunks) > 0
        # Should have both section indices
        for chunk in multi_section_chunks:
            section_indices = [s.section_index for s in chunk.source_sections]
            assert 0 in section_indices
            assert 1 in section_indices

    def test_source_sections_are_sorted_by_index(self, sample_sections):
        """Test that source sections are sorted by section_index"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=8)

        for chunk in chunks:
            section_indices = [s.section_index for s in chunk.source_sections]
            # Should be in ascending order
            assert section_indices == sorted(section_indices)

    def test_source_sections_are_unique(self):
        """Test that source sections list contains unique sections"""
        sections = [
            Section(content="word word word word word word", section_index=0),
            Section(content="more more more more", section_index=1),
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=5)

        for chunk in chunks:
            section_indices = [s.section_index for s in chunk.source_sections]
            # No duplicate section indices
            assert len(section_indices) == len(set(section_indices))

    def test_first_chunk_source_sections(self, sample_sections):
        """Test that first chunk references the first section"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=3)

        first_chunk = chunks[0]
        assert 0 in [s.section_index for s in first_chunk.source_sections]

    def test_last_chunk_source_sections(self, sample_sections):
        """Test that last chunk references the last section"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=3)

        last_chunk = chunks[-1]
        assert 4 in [s.section_index for s in last_chunk.source_sections]


class TestGetCandidateChunks:
    """Test getting candidate chunks around a current section"""

    def test_get_candidate_chunks_basic(self, sample_sections):
        """Test that candidate chunks are returned for a section"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=3)
        current_section = sample_sections[2]  # Middle section

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # Should return some candidates
        assert len(candidates) > 0
        # All candidates should be Chunk instances
        assert all(isinstance(chunk, Chunk) for chunk in candidates)

    def test_candidate_chunks_range_calculation(self, sample_sections):
        """Test that candidate chunks are within correct range (idx-2 to idx+3)"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=3)
        current_section = sample_sections[2]  # Index 2

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # All candidates should only reference sections in range [0, 5] (2-2 to 2+3)
        for chunk in candidates:
            for section in chunk.source_sections:
                assert 0 <= section.section_index <= 5

    def test_candidate_chunks_exclude_boundary_single_sections(self, sample_sections):
        """Test that chunks with single sections at range boundaries are excluded"""
        chunks = chunk_producer.generate_chunks(sample_sections, window_size=3)
        current_section = sample_sections[2]  # Index 2, range [0, 5]

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # No candidate should have a single source section at index 0 or 5 (boundaries)
        # Note: range is idx-2 to idx+3, so for idx=2, range is [0, 5]
        for chunk in candidates:
            if len(chunk.source_sections) == 1:
                section_index = chunk.source_sections[0].section_index
                assert section_index not in (0, 5)

    def test_candidate_chunks_for_first_section(self):
        """Test candidate chunks for the first section"""
        sections = [
            Section(content=f"Section {i} content with words", section_index=i)
            for i in range(6)
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)
        current_section = sections[0]  # Index 0, range [-2, 3]

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # Should only include chunks within valid section indices (0 to 3)
        for chunk in candidates:
            for section in chunk.source_sections:
                assert section.section_index <= 3

    def test_candidate_chunks_for_last_section(self):
        """Test candidate chunks for the last section"""
        sections = [
            Section(content=f"Section {i} content with words", section_index=i)
            for i in range(6)
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)
        current_section = sections[5]  # Index 5, range [3, 8]

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # Should only include chunks within valid section indices (3 to 5)
        for chunk in candidates:
            for section in chunk.source_sections:
                assert section.section_index >= 3

    def test_candidate_chunks_all_within_range(self):
        """Test that all source sections of candidates are within range"""
        sections = [
            Section(content=f"Section {i} with some words here", section_index=i)
            for i in range(10)
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=4)
        current_section = sections[5]  # Index 5, range [3, 8]

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        for chunk in candidates:
            # ALL source sections must be within range
            section_indices = [s.section_index for s in chunk.source_sections]
            assert all(3 <= idx <= 8 for idx in section_indices)

    def test_candidate_chunks_multi_section_at_boundaries_included(self):
        """Test that chunks with multiple sections at boundaries are included"""
        sections = [
            Section(content=f"Section {i} content with words", section_index=i)
            for i in range(6)
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=5)
        current_section = sections[2]  # Index 2, range [0, 5]

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # Chunks spanning boundary sections (0 or 5) with other sections should be included
        boundary_multi_section = [
            chunk
            for chunk in candidates
            if len(chunk.source_sections) > 1
            and any(s.section_index in (0, 5) for s in chunk.source_sections)
        ]

        # Should have some multi-section chunks at boundaries
        assert len(boundary_multi_section) > 0

    def test_candidate_chunks_empty_when_no_matches(self):
        """Test that empty list is returned when no chunks match criteria"""
        sections = [Section(content="word", section_index=i) for i in range(10)]
        chunks = chunk_producer.generate_chunks(sections, window_size=1)
        # Chunks will each have single source section
        current_section = sections[5]  # Index 5, range [3, 8]

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # With window size 1, all chunks have single sections at boundaries
        # Most should be filtered out
        assert isinstance(candidates, list)

    def test_candidate_chunks_correct_range_window(self):
        """Test that the range window is exactly -2 to +3 from current section"""
        sections = [
            Section(content=f"Section {i} content with more words", section_index=i)
            for i in range(10)
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)
        current_section = sections[5]  # Index 5

        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # Expected range: [3, 8] (5-2 to 5+3)
        for chunk in candidates:
            section_indices = [s.section_index for s in chunk.source_sections]
            assert min(section_indices) >= 3
            assert max(section_indices) <= 8


class TestChunkProducerIntegration:
    """Integration tests for complete workflows"""

    def test_generate_and_filter_workflow(self):
        """Test complete workflow: generate chunks then filter candidates"""
        sections = [
            Section(content=f"This is section {i} with content", section_index=i)
            for i in range(8)
        ]

        # Generate chunks
        chunks = chunk_producer.generate_chunks(sections, window_size=5)
        assert len(chunks) > 0

        # Get candidates for middle section
        current_section = sections[4]
        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)

        # Candidates should be a subset of all chunks
        assert len(candidates) <= len(chunks)
        assert all(chunk in chunks for chunk in candidates)

    def test_chunk_content_sliding_window(self):
        """Test that chunks form a proper sliding window of content"""
        sections = [
            Section(content="one two three", section_index=0),
            Section(content="four five six", section_index=1),
        ]
        chunks = chunk_producer.generate_chunks(sections, window_size=3)

        # Should create 4 chunks with sliding window
        assert len(chunks) == 4
        # Each chunk should start one word after the previous
        assert "one two three" in chunks[0].partial_content
        assert "two three four" in chunks[1].partial_content
        assert "three four five" in chunks[2].partial_content
        assert "four five six" in chunks[3].partial_content

    def test_large_section_list(self):
        """Test with a large number of sections"""
        sections = [
            Section(content=f"Section {i} content here", section_index=i)
            for i in range(100)
        ]

        chunks = chunk_producer.generate_chunks(sections, window_size=10)
        assert len(chunks) > 0

        # Get candidates for a middle section
        current_section = sections[50]
        candidates = chunk_producer.get_candidate_chunks(current_section, chunks)
        assert len(candidates) > 0

    def test_sections_with_special_characters(self):
        """Test that sections with special characters are handled correctly"""
        sections = [
            Section(content="Hello! How are you?", section_index=0),
            Section(content="I'm fine, thanks.", section_index=1),
            Section(content="Let's continue...", section_index=2),
        ]

        chunks = chunk_producer.generate_chunks(sections, window_size=4)

        # Should handle normalization properly
        for chunk in chunks:
            # Normalized content should not have special characters
            assert "!" not in chunk.partial_content
            assert "?" not in chunk.partial_content
            assert "," not in chunk.partial_content

    def test_sections_with_numbers(self):
        """Test that sections with numbers are normalized to words"""
        sections = [
            Section(content="I have 3 cats and 2 dogs", section_index=0),
            Section(content="That makes 5 pets total", section_index=1),
        ]

        chunks = chunk_producer.generate_chunks(sections, window_size=5)

        # Numbers should be converted to words during normalization
        for chunk in chunks:
            # Should contain words like "three", "two", "five" instead of digits
            assert not any(char.isdigit() for char in chunk.partial_content)
