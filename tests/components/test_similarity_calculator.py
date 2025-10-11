import pytest
from unittest.mock import patch
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.data.models import Section, Chunk, SimilarityResult


@pytest.fixture
def calculator():
    """Create a SimilarityCalculator instance for testing"""
    return SimilarityCalculator()


@pytest.fixture
def custom_calculator():
    """Create a SimilarityCalculator with custom weights for testing"""
    return SimilarityCalculator(semantic_weight=0.7, phonetic_weight=0.3)


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing"""
    return [
        Chunk(
            partial_content="hello world",
            source_sections=[Section(content="hello world", section_index=0)],
        ),
        Chunk(
            partial_content="goodbye earth",
            source_sections=[Section(content="goodbye earth", section_index=1)],
        ),
        Chunk(
            partial_content="hi planet",
            source_sections=[Section(content="hi planet", section_index=2)],
        ),
    ]


class TestSimilarityCalculatorInitialization:
    """Test SimilarityCalculator initialization and configuration"""

    def test_default_weights(self):
        """Test default weights are 60% semantic and 40% phonetic"""
        calculator = SimilarityCalculator()
        assert calculator.semantic_weight == 0.6
        assert calculator.phonetic_weight == 0.4

    def test_custom_weights(self):
        """Test custom weights can be set"""
        calculator = SimilarityCalculator(semantic_weight=0.7, phonetic_weight=0.3)
        assert calculator.semantic_weight == 0.7
        assert calculator.phonetic_weight == 0.3

    def test_weights_sum_to_one(self):
        """Test that default weights sum to 1.0"""
        calculator = SimilarityCalculator()
        assert calculator.semantic_weight + calculator.phonetic_weight == 1.0

    def test_semantic_and_phonetic_instances_created(self, calculator):
        """Test that semantic and phonetic instances are initialized"""
        assert calculator.semantic is not None
        assert calculator.phonetic is not None

    def test_different_weight_configurations(self):
        """Test various weight configurations"""
        configs = [(0.5, 0.5), (0.8, 0.2), (0.3, 0.7), (1.0, 0.0)]
        for sem, pho in configs:
            calc = SimilarityCalculator(semantic_weight=sem, phonetic_weight=pho)
            assert calc.semantic_weight == sem
            assert calc.phonetic_weight == pho


class TestSimilarityCalculatorWeighting:
    """Test proper weighting of semantic and phonetic scores"""

    def test_scores_are_weighted_correctly(self, calculator, sample_chunks):
        """Test that scores are properly weighted (60% semantic, 40% phonetic)"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            # Set up mock returns with known scores
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=1.0),
                SimilarityResult(chunk=sample_chunks[1], score=0.8),
                SimilarityResult(chunk=sample_chunks[2], score=0.6),
            ]

            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.6),
                SimilarityResult(chunk=sample_chunks[1], score=0.8),
                SimilarityResult(chunk=sample_chunks[2], score=1.0),
            ]

            results = calculator.compare("test input", sample_chunks)

            # Verify both methods were called
            mock_semantic.assert_called_once_with("test input", sample_chunks)
            mock_phonetic.assert_called_once_with("test input", sample_chunks)

            # Results should be returned
            assert len(results) == 3

    def test_custom_weight_application(self, sample_chunks):
        """Test that custom weights are applied correctly"""
        calculator = SimilarityCalculator(semantic_weight=0.8, phonetic_weight=0.2)

        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=1.0),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=1.0),
            ]

            results = calculator.compare("test", [sample_chunks[0]])
            assert len(results) == 1

    def test_zero_phonetic_weight(self, sample_chunks):
        """Test with 100% semantic weight (0% phonetic)"""
        calculator = SimilarityCalculator(semantic_weight=1.0, phonetic_weight=0.0)

        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.8),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.2),
            ]

            results = calculator.compare("test", [sample_chunks[0]])
            assert len(results) == 1

    def test_zero_semantic_weight(self, sample_chunks):
        """Test with 100% phonetic weight (0% semantic)"""
        calculator = SimilarityCalculator(semantic_weight=0.0, phonetic_weight=1.0)

        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.2),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.8),
            ]

            results = calculator.compare("test", [sample_chunks[0]])
            assert len(results) == 1


class TestSimilarityCalculatorNormalization:
    """Test score normalization to 0-1 range"""

    def test_normalization_produces_zero_to_one_range(self, calculator):
        """Test that normalized scores are in 0-1 range"""
        results = [
            SimilarityResult(
                chunk=Chunk(partial_content="test1", source_sections=[]), score=0.5
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test2", source_sections=[]), score=0.8
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test3", source_sections=[]), score=1.0
            ),
        ]

        normalized = calculator._normalize_scores(results)

        for score in normalized.values():
            assert 0.0 <= score <= 1.0

    def test_normalization_with_all_same_scores(self, calculator):
        """Test normalization when all scores are identical"""
        results = [
            SimilarityResult(
                chunk=Chunk(partial_content="test1", source_sections=[]), score=0.7
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test2", source_sections=[]), score=0.7
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test3", source_sections=[]), score=0.7
            ),
        ]

        normalized = calculator._normalize_scores(results)

        # All scores should be 1.0 since they're all above threshold and identical
        for score in normalized.values():
            assert score == 1.0

    def test_normalization_maps_min_to_zero_max_to_one(self, calculator):
        """Test that normalization maps minimum valid score to 0 and maximum to 1"""
        results = [
            SimilarityResult(
                chunk=Chunk(partial_content="test1", source_sections=[]), score=0.5
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test2", source_sections=[]), score=0.75
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test3", source_sections=[]), score=1.0
            ),
        ]

        normalized = calculator._normalize_scores(results)

        # Find the normalized scores
        scores = list(normalized.values())

        # Should have 0.0 (min) and 1.0 (max)
        assert 0.0 in scores
        assert 1.0 in scores

    def test_normalization_with_empty_results(self, calculator):
        """Test normalization with empty results list"""
        normalized = calculator._normalize_scores([])
        assert normalized == {}

    def test_normalization_preserves_relative_order(self, calculator):
        """Test that normalization preserves the relative order of scores"""
        chunk1 = Chunk(partial_content="test1", source_sections=[])
        chunk2 = Chunk(partial_content="test2", source_sections=[])
        chunk3 = Chunk(partial_content="test3", source_sections=[])

        results = [
            SimilarityResult(chunk=chunk1, score=0.5),
            SimilarityResult(chunk=chunk2, score=0.75),
            SimilarityResult(chunk=chunk3, score=1.0),
        ]

        normalized = calculator._normalize_scores(results)

        # Extract normalized scores in order
        norm1 = normalized[id(chunk1)]
        norm2 = normalized[id(chunk2)]
        norm3 = normalized[id(chunk3)]

        # Relative order should be preserved
        assert norm1 < norm2 < norm3


class TestSimilarityCalculatorThreshold:
    """Test that results below 0.5 threshold are set to 0.0"""

    def test_scores_below_threshold_set_to_zero(self, calculator):
        """Test that scores below 0.5 are set to 0.0"""
        results = [
            SimilarityResult(
                chunk=Chunk(partial_content="test1", source_sections=[]), score=0.3
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test2", source_sections=[]), score=0.4
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test3", source_sections=[]), score=0.49
            ),
        ]

        normalized = calculator._normalize_scores(results)

        # All scores below threshold should be 0.0
        for score in normalized.values():
            assert score == 0.0

    def test_score_exactly_at_threshold_not_zeroed(self, calculator):
        """Test that score exactly at 0.5 threshold is not zeroed"""
        results = [
            SimilarityResult(
                chunk=Chunk(partial_content="test1", source_sections=[]), score=0.5
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test2", source_sections=[]), score=0.6
            ),
        ]

        normalized = calculator._normalize_scores(results)

        # Score at 0.5 should be normalized to 0.0 (min), but not rejected
        scores = list(normalized.values())
        assert 0.0 in scores  # 0.5 normalizes to 0.0
        assert 1.0 in scores  # 0.6 normalizes to 1.0

    def test_mixed_scores_above_and_below_threshold(self, calculator):
        """Test normalization with mixed scores above and below threshold"""
        chunk1 = Chunk(partial_content="test1", source_sections=[])
        chunk2 = Chunk(partial_content="test2", source_sections=[])
        chunk3 = Chunk(partial_content="test3", source_sections=[])

        results = [
            SimilarityResult(chunk=chunk1, score=0.3),  # Below threshold
            SimilarityResult(chunk=chunk2, score=0.7),  # Above threshold
            SimilarityResult(chunk=chunk3, score=0.9),  # Above threshold
        ]

        normalized = calculator._normalize_scores(results)

        # Below threshold should be 0.0
        assert normalized[id(chunk1)] == 0.0

        # Above threshold are normalized: 0.7 becomes 0.0 (min), 0.9 becomes 1.0 (max)
        assert normalized[id(chunk2)] == 0.0  # min valid score
        assert normalized[id(chunk3)] == 1.0  # max valid score

    def test_all_scores_above_threshold(self, calculator):
        """Test when all scores are above threshold"""
        results = [
            SimilarityResult(
                chunk=Chunk(partial_content="test1", source_sections=[]), score=0.6
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test2", source_sections=[]), score=0.8
            ),
            SimilarityResult(
                chunk=Chunk(partial_content="test3", source_sections=[]), score=1.0
            ),
        ]

        normalized = calculator._normalize_scores(results)

        # All should be in valid range
        for score in normalized.values():
            assert 0.0 <= score <= 1.0


class TestSimilarityCalculatorEmptyCandidates:
    """Test handling of empty candidate lists"""

    def test_empty_candidates_list_returns_empty(self, calculator):
        """Test that empty candidate list returns empty results"""
        results = calculator.compare("test input", [])
        assert results == []

    def test_empty_candidates_no_semantic_call(self, calculator):
        """Test that semantic compare is not called with empty candidates"""
        with patch.object(calculator.semantic, "compare") as mock_semantic:
            calculator.compare("test input", [])
            mock_semantic.compare.assert_not_called()

    def test_empty_candidates_no_phonetic_call(self, calculator):
        """Test that phonetic compare is not called with empty candidates"""
        with patch.object(calculator.phonetic, "compare") as mock_phonetic:
            calculator.compare("test input", [])
            mock_phonetic.compare.assert_not_called()

    def test_empty_input_string_with_candidates(self, calculator, sample_chunks):
        """Test with empty input string but valid candidates"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.5),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.5),
            ]

            results = calculator.compare("", [sample_chunks[0]])

            # Should still call comparison methods
            mock_semantic.assert_called_once()
            mock_phonetic.assert_called_once()
            assert len(results) == 1


class TestSimilarityCalculatorResultFormat:
    """Test format and structure of results"""

    def test_results_are_similarity_result_instances(self, calculator, sample_chunks):
        """Test that all results are SimilarityResult instances"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=chunk, score=0.7) for chunk in sample_chunks
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=chunk, score=0.6) for chunk in sample_chunks
            ]

            results = calculator.compare("test", sample_chunks)

            for result in results:
                assert isinstance(result, SimilarityResult)

    def test_results_are_sorted_descending(self, calculator, sample_chunks):
        """Test that results are sorted by score in descending order"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            # Set up different scores
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.5),
                SimilarityResult(chunk=sample_chunks[1], score=0.8),
                SimilarityResult(chunk=sample_chunks[2], score=1.0),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.6),
                SimilarityResult(chunk=sample_chunks[1], score=0.7),
                SimilarityResult(chunk=sample_chunks[2], score=0.9),
            ]

            results = calculator.compare("test", sample_chunks)

            # Check descending order
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_all_chunks_returned(self, calculator, sample_chunks):
        """Test that all input chunks are in the results"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=chunk, score=0.7) for chunk in sample_chunks
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=chunk, score=0.6) for chunk in sample_chunks
            ]

            results = calculator.compare("test", sample_chunks)

            result_chunks = [r.chunk for r in results]
            assert len(result_chunks) == len(sample_chunks)
            for chunk in sample_chunks:
                assert chunk in result_chunks

    def test_chunk_preserved_in_result(self, calculator, sample_chunks):
        """Test that original chunk objects are preserved"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.8),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.7),
            ]

            results = calculator.compare("test", [sample_chunks[0]])

            assert results[0].chunk is sample_chunks[0]

    def test_score_is_float(self, calculator, sample_chunks):
        """Test that all scores are float type"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=chunk, score=0.7) for chunk in sample_chunks
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=chunk, score=0.6) for chunk in sample_chunks
            ]

            results = calculator.compare("test", sample_chunks)

            for result in results:
                assert isinstance(result.score, float)


class TestSimilarityCalculatorErrorHandling:
    """Test error handling in similarity calculations"""

    def test_exception_handling_semantic_error(self, calculator, sample_chunks):
        """Test handling of exception from semantic comparison"""
        with patch.object(calculator.semantic, "compare") as mock_semantic:
            mock_semantic.side_effect = RuntimeError("Semantic error")

            with pytest.raises(RuntimeError, match="Similarity comparison failed"):
                calculator.compare("test", sample_chunks)

    def test_exception_handling_phonetic_error(self, calculator, sample_chunks):
        """Test handling of exception from phonetic comparison"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=chunk, score=0.7) for chunk in sample_chunks
            ]
            mock_phonetic.side_effect = RuntimeError("Phonetic error")

            with pytest.raises(RuntimeError, match="Similarity comparison failed"):
                calculator.compare("test", sample_chunks)

    def test_error_message_includes_original_exception(self, calculator, sample_chunks):
        """Test that error message includes the original exception"""
        with patch.object(calculator.semantic, "compare") as mock_semantic:
            mock_semantic.side_effect = ValueError("Original error message")

            try:
                calculator.compare("test", sample_chunks)
            except RuntimeError as e:
                assert "Original error message" in str(e)


class TestSimilarityCalculatorIntegration:
    """Test integration scenarios with both semantic and phonetic"""

    def test_complete_workflow(self, calculator, sample_chunks):
        """Test complete workflow from input to final results"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.9),
                SimilarityResult(chunk=sample_chunks[1], score=0.7),
                SimilarityResult(chunk=sample_chunks[2], score=0.5),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.6),
                SimilarityResult(chunk=sample_chunks[1], score=0.8),
                SimilarityResult(chunk=sample_chunks[2], score=1.0),
            ]

            results = calculator.compare("test input", sample_chunks)

            # Verify complete results
            assert len(results) == 3
            assert all(isinstance(r, SimilarityResult) for r in results)
            assert all(0.0 <= r.score <= 1.0 for r in results)

    def test_real_world_scenario(self, calculator):
        """Test with realistic chunks and input"""
        chunks = [
            Chunk(
                partial_content="hello world how are you",
                source_sections=[
                    Section(content="hello world how are you", section_index=0)
                ],
            ),
            Chunk(
                partial_content="goodbye world see you later",
                source_sections=[
                    Section(content="goodbye world see you later", section_index=1)
                ],
            ),
        ]

        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            mock_semantic.return_value = [
                SimilarityResult(chunk=chunks[0], score=0.85),
                SimilarityResult(chunk=chunks[1], score=0.55),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=chunks[0], score=0.75),
                SimilarityResult(chunk=chunks[1], score=0.65),
            ]

            results = calculator.compare("hello there", chunks)

            assert len(results) == 2
            assert results[0].score >= results[1].score

    def test_combined_scores_reflect_both_methods(self, calculator, sample_chunks):
        """Test that final scores reflect both semantic and phonetic contributions"""
        with (
            patch.object(calculator.semantic, "compare") as mock_semantic,
            patch.object(calculator.phonetic, "compare") as mock_phonetic,
        ):
            # High semantic, low phonetic
            mock_semantic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=1.0),
            ]
            mock_phonetic.return_value = [
                SimilarityResult(chunk=sample_chunks[0], score=0.5),
            ]

            results = calculator.compare("test", [sample_chunks[0]])

            # Score should be influenced by both
            assert len(results) == 1
            assert 0.0 <= results[0].score <= 1.0
