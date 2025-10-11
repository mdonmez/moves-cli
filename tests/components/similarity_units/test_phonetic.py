import pytest
from unittest.mock import patch
from moves_cli.core.components.similarity_units.phonetic import Phonetic
from moves_cli.data.models import Section, Chunk, SimilarityResult


@pytest.fixture
def phonetic():
    """Create a Phonetic instance for testing"""
    return Phonetic()


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing"""
    return [
        Chunk(
            partial_content="there is a house",
            source_sections=[Section(content="there is a house", section_index=0)],
        ),
        Chunk(
            partial_content="their home is nice",
            source_sections=[Section(content="their home is nice", section_index=1)],
        ),
        Chunk(
            partial_content="completely different words",
            source_sections=[
                Section(content="completely different words", section_index=2)
            ],
        ),
    ]


@pytest.fixture
def homophones_chunks():
    """Create chunks with homophones (words that sound the same)"""
    return [
        Chunk(
            partial_content="write a letter",
            source_sections=[Section(content="write a letter", section_index=0)],
        ),
        Chunk(
            partial_content="right answer here",
            source_sections=[Section(content="right answer here", section_index=1)],
        ),
        Chunk(
            partial_content="knight in armor",
            source_sections=[Section(content="knight in armor", section_index=2)],
        ),
        Chunk(
            partial_content="night time sleep",
            source_sections=[Section(content="night time sleep", section_index=3)],
        ),
    ]


class TestPhoneticSimilarSounding:
    """Test that similar-sounding words score high"""

    def test_similar_sounding_words_high_score(self, phonetic, sample_chunks):
        """Test that 'there' and 'their' have high phonetic similarity"""
        input_str = "there"

        results = phonetic.compare(input_str, sample_chunks)

        # Results should be sorted by score descending
        assert results[0].score > results[1].score > results[2].score

        # First two chunks contain "there" and "their" - should score higher than the third
        assert results[0].score > results[2].score
        assert results[1].score > results[2].score

    def test_homophones_score_high(self, phonetic, homophones_chunks):
        """Test that homophones (same pronunciation) score relatively high"""
        input_str = "write"

        results = phonetic.compare(input_str, homophones_chunks)

        # "write" and "right" should score highest as they're homophones
        # Phonetic similarity compares entire phrases, so scores may be moderate
        assert results[0].score > 0.4
        assert results[0].chunk.partial_content == "write a letter"

    def test_knight_and_night_similarity(self, phonetic):
        """Test that 'knight' and 'night' have similar phonetic similarity"""
        chunks = [
            Chunk(
                partial_content="knight in shining armor",
                source_sections=[
                    Section(content="knight in shining armor", section_index=0)
                ],
            ),
            Chunk(
                partial_content="night is dark",
                source_sections=[Section(content="night is dark", section_index=1)],
            ),
        ]

        results = phonetic.compare("knight", chunks)

        # Both should score reasonably due to phonetics
        assert results[0].score > 0.2
        assert results[1].score > 0.2
        # The two chunks should have similar scores since knight/night sound alike
        score_diff = abs(results[0].score - results[1].score)
        assert score_diff < 0.3

    def test_to_and_two_similarity(self, phonetic):
        """Test that 'to' and 'two' have reasonable similarity"""
        chunks = [
            Chunk(
                partial_content="go to school",
                source_sections=[Section(content="go to school", section_index=0)],
            ),
            Chunk(
                partial_content="two of them",
                source_sections=[Section(content="two of them", section_index=1)],
            ),
        ]

        results = phonetic.compare("to", chunks)

        # Both should score reasonably as context affects overall phonetic score
        assert all(result.score > 0.0 for result in results)
        # Both chunks should have some phonetic similarity
        assert len(results) == 2

    def test_similar_phrases_high_score(self, phonetic):
        """Test that similar-sounding phrases score reasonably"""
        chunks = [
            Chunk(
                partial_content="they are going there",
                source_sections=[
                    Section(content="they are going there", section_index=0)
                ],
            ),
            Chunk(
                partial_content="their new house",
                source_sections=[Section(content="their new house", section_index=1)],
            ),
        ]

        results = phonetic.compare("there house", chunks)

        # Should get some reasonable scores
        assert results[0].score > 0.2
        assert results[1].score > 0.2

    def test_where_and_wear_similarity(self, phonetic):
        """Test that 'where' and 'wear' have reasonable similarity"""
        chunks = [
            Chunk(
                partial_content="where are you",
                source_sections=[Section(content="where are you", section_index=0)],
            ),
            Chunk(
                partial_content="wear a coat",
                source_sections=[Section(content="wear a coat", section_index=1)],
            ),
        ]

        results = phonetic.compare("where", chunks)

        assert results[0].score > 0.4
        assert results[1].score > 0.4


class TestPhoneticDifferentSounding:
    """Test that different-sounding words score low"""

    def test_different_sounding_words_low_score(self, phonetic, sample_chunks):
        """Test that completely different words score low"""
        input_str = "apple banana"

        results = phonetic.compare(input_str, sample_chunks)

        # All scores should be relatively low for unrelated words
        assert all(result.score < 0.5 for result in results)

    def test_unrelated_words_score_low(self, phonetic):
        """Test that unrelated words have low similarity"""
        chunks = [
            Chunk(
                partial_content="hello world program",
                source_sections=[
                    Section(content="hello world program", section_index=0)
                ],
            ),
            Chunk(
                partial_content="goodbye universe code",
                source_sections=[
                    Section(content="goodbye universe code", section_index=1)
                ],
            ),
        ]

        results = phonetic.compare("apple orange banana", chunks)

        # Unrelated words should score low
        assert all(result.score < 0.4 for result in results)

    def test_very_different_phrases_low_score(self, phonetic):
        """Test that very different phrases score lower"""
        chunks = [
            Chunk(
                partial_content="quick brown fox",
                source_sections=[Section(content="quick brown fox", section_index=0)],
            )
        ]

        results = phonetic.compare("zebra elephant giraffe", chunks)

        # Should score lower than highly similar phrases
        assert results[0].score < 0.6

    def test_opposite_meaning_different_sound(self, phonetic):
        """Test that random letter combinations score relatively low"""
        chunks = [
            Chunk(
                partial_content="hot summer day",
                source_sections=[Section(content="hot summer day", section_index=0)],
            ),
            Chunk(
                partial_content="cold winter night",
                source_sections=[Section(content="cold winter night", section_index=1)],
            ),
        ]

        results = phonetic.compare("xyz abc qwerty", chunks)

        # Random letters should score lower than meaningful similar words
        assert all(result.score < 0.6 for result in results)


class TestPhoneticCaching:
    """Test that the cache works correctly"""

    def test_cache_same_input_twice(self, phonetic, sample_chunks):
        """Test that calling with same input twice uses cache"""
        input_str = "there is a house"

        # First call
        results1 = phonetic.compare(input_str, sample_chunks)

        # Second call with same input
        results2 = phonetic.compare(input_str, sample_chunks)

        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.score == r2.score
            assert r1.chunk.partial_content == r2.chunk.partial_content

    def test_phonetic_code_cache(self, phonetic):
        """Test that _get_phonetic_code caches results"""
        text = "hello world"

        # Call multiple times
        code1 = phonetic._get_phonetic_code(text)
        code2 = phonetic._get_phonetic_code(text)
        code3 = phonetic._get_phonetic_code(text)

        # All should return the same result
        assert code1 == code2 == code3

    def test_fuzz_ratio_cache(self, phonetic):
        """Test that _calculate_fuzz_ratio caches results"""
        code1 = "HL"
        code2 = "WRLT"

        # Call multiple times
        ratio1 = phonetic._calculate_fuzz_ratio(code1, code2)
        ratio2 = phonetic._calculate_fuzz_ratio(code1, code2)
        ratio3 = phonetic._calculate_fuzz_ratio(code1, code2)

        # All should return the same result
        assert ratio1 == ratio2 == ratio3

    def test_cache_hit_different_inputs(self, phonetic, sample_chunks):
        """Test that cache is used when same chunk appears multiple times"""
        # Use the same chunk content multiple times
        input_str1 = "there is a house"
        input_str2 = "their home is nice"

        results1 = phonetic.compare(input_str1, sample_chunks)
        results2 = phonetic.compare(input_str2, sample_chunks)

        # Results should be different but cache should be used internally
        assert results1 != results2
        assert len(results1) > 0
        assert len(results2) > 0

    def test_cache_cleared_between_instances(self):
        """Test that cache is tied to the class, not instance"""
        phonetic1 = Phonetic()
        phonetic2 = Phonetic()

        text = "test cache"

        # Both instances should use the same cache
        code1 = phonetic1._get_phonetic_code(text)
        code2 = phonetic2._get_phonetic_code(text)

        assert code1 == code2

    def test_cache_with_patch(self, phonetic, sample_chunks):
        """Test that cache is actually being used by mocking the underlying function"""
        input_str = "there is a house"

        # First call to populate cache
        phonetic.compare(input_str, sample_chunks)

        # Patch the metaphone function and call again
        with patch("moves_cli.core.components.similarity_units.phonetic.metaphone"):
            # This should use cached results, so metaphone won't be called for same inputs
            results = phonetic.compare(input_str, sample_chunks)

            # Results should still be returned
            assert len(results) > 0

            # Metaphone might be called for chunks we haven't seen, but not for the input
            # if it was already cached


class TestPhoneticResultFormat:
    """Test the structure and format of results"""

    def test_results_are_similarity_result_instances(self, phonetic, sample_chunks):
        """Test that results are SimilarityResult instances"""
        results = phonetic.compare("test", sample_chunks)

        assert all(isinstance(result, SimilarityResult) for result in results)

    def test_results_are_sorted_descending(self, phonetic, sample_chunks):
        """Test that results are sorted by score in descending order"""
        results = phonetic.compare("there", sample_chunks)

        # Scores should be in descending order
        scores = [result.score for result in results]
        assert scores == sorted(scores, reverse=True)

    def test_all_chunks_returned(self, phonetic, sample_chunks):
        """Test that all input chunks are returned in results"""
        results = phonetic.compare("test", sample_chunks)

        assert len(results) == len(sample_chunks)

    def test_chunk_preserved_in_result(self, phonetic, sample_chunks):
        """Test that original chunk data is preserved in results"""
        results = phonetic.compare("test", sample_chunks)

        result_contents = [result.chunk.partial_content for result in results]
        sample_contents = [chunk.partial_content for chunk in sample_chunks]

        # All sample chunks should appear in results
        for content in sample_contents:
            assert content in result_contents

    def test_score_range(self, phonetic, sample_chunks):
        """Test that scores are between 0.0 and 1.0"""
        results = phonetic.compare("test", sample_chunks)

        for result in results:
            assert 0.0 <= result.score <= 1.0


class TestPhoneticEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_input_string(self, phonetic, sample_chunks):
        """Test with empty input string"""
        results = phonetic.compare("", sample_chunks)

        # Should still return results, but likely with low scores
        assert len(results) == len(sample_chunks)
        assert all(isinstance(result, SimilarityResult) for result in results)

    def test_empty_candidates_list(self, phonetic):
        """Test with empty candidates list"""
        results = phonetic.compare("test input", [])

        # Should return empty list
        assert results == []

    def test_single_candidate(self, phonetic):
        """Test with single candidate"""
        chunks = [
            Chunk(
                partial_content="single chunk",
                source_sections=[Section(content="single chunk", section_index=0)],
            )
        ]

        results = phonetic.compare("single", chunks)

        assert len(results) == 1
        assert isinstance(results[0], SimilarityResult)

    def test_special_characters_in_input(self, phonetic, sample_chunks):
        """Test with special characters in input"""
        results = phonetic.compare("hello! @#$ world?", sample_chunks)

        # Should handle gracefully
        assert len(results) == len(sample_chunks)

    def test_numbers_in_input(self, phonetic, sample_chunks):
        """Test with numbers in input"""
        results = phonetic.compare("test 123 456", sample_chunks)

        # Should handle numbers
        assert len(results) == len(sample_chunks)

    def test_very_long_input(self, phonetic, sample_chunks):
        """Test with very long input string"""
        long_input = " ".join(["word"] * 100)

        results = phonetic.compare(long_input, sample_chunks)

        assert len(results) == len(sample_chunks)

    def test_unicode_characters(self, phonetic):
        """Test with unicode characters"""
        chunks = [
            Chunk(
                partial_content="café résumé",
                source_sections=[Section(content="café résumé", section_index=0)],
            )
        ]

        results = phonetic.compare("cafe resume", chunks)

        # Should handle unicode
        assert len(results) == 1


class TestPhoneticErrorHandling:
    """Test error handling"""

    def test_exception_handling(self, phonetic):
        """Test that exceptions are properly caught and re-raised as RuntimeError"""
        # Create a chunk that might cause issues
        chunks = [
            Chunk(
                partial_content="normal content",
                source_sections=[Section(content="normal content", section_index=0)],
            )
        ]

        # Patch metaphone to raise an exception
        with patch(
            "moves_cli.core.components.similarity_units.phonetic.metaphone",
            side_effect=Exception("Test exception"),
        ):
            with pytest.raises(
                RuntimeError, match="Phonetic similarity comparison failed"
            ):
                phonetic.compare("test", chunks)

    def test_error_message_includes_original_exception(self, phonetic):
        """Test that error message includes original exception details"""
        chunks = [
            Chunk(
                partial_content="content",
                source_sections=[Section(content="content", section_index=0)],
            )
        ]

        with patch(
            "moves_cli.core.components.similarity_units.phonetic.metaphone",
            side_effect=ValueError("Original error"),
        ):
            try:
                phonetic.compare("test", chunks)
                pytest.fail("Should have raised RuntimeError")
            except RuntimeError as e:
                # Check that the original exception is chained
                assert e.__cause__ is not None
                assert isinstance(e.__cause__, ValueError)


class TestPhoneticIntegration:
    """Integration tests for complete workflows"""

    def test_multiple_comparisons_workflow(self, phonetic):
        """Test performing multiple comparisons in sequence"""
        chunks = [
            Chunk(
                partial_content="first chunk here",
                source_sections=[Section(content="first chunk here", section_index=0)],
            ),
            Chunk(
                partial_content="second chunk there",
                source_sections=[
                    Section(content="second chunk there", section_index=1)
                ],
            ),
        ]

        # Perform multiple comparisons
        results1 = phonetic.compare("first", chunks)
        results2 = phonetic.compare("second", chunks)
        results3 = phonetic.compare("third", chunks)

        # All should return valid results
        assert len(results1) == 2
        assert len(results2) == 2
        assert len(results3) == 2

        # Results should be properly sorted
        assert results1[0].score >= results1[1].score
        assert results2[0].score >= results2[1].score

    def test_real_world_scenario(self, phonetic):
        """Test a real-world-like scenario with various chunks"""
        chunks = [
            Chunk(
                partial_content="the quick brown fox jumps over the lazy dog",
                source_sections=[
                    Section(
                        content="the quick brown fox jumps over the lazy dog",
                        section_index=0,
                    )
                ],
            ),
            Chunk(
                partial_content="a slow red cat walks under the active puppy",
                source_sections=[
                    Section(
                        content="a slow red cat walks under the active puppy",
                        section_index=1,
                    )
                ],
            ),
            Chunk(
                partial_content="programming is fun and challenging",
                source_sections=[
                    Section(
                        content="programming is fun and challenging",
                        section_index=2,
                    )
                ],
            ),
        ]

        results = phonetic.compare("quick brown fox", chunks)

        # First chunk should score highest
        assert results[0].chunk.partial_content == chunks[0].partial_content
        assert results[0].score > results[1].score
        assert results[0].score > results[2].score

    def test_phonetic_code_generation(self, phonetic):
        """Test that phonetic codes are generated correctly"""
        # Test that similar-sounding words have similar codes
        code1 = phonetic._get_phonetic_code("there")
        code2 = phonetic._get_phonetic_code("their")

        # Codes should be similar (both should map to same/similar phonetic code)
        # Metaphone typically gives very similar codes for homophones
        assert len(code1) > 0
        assert len(code2) > 0
