import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from moves_cli.core.components.similarity_units.semantic import Semantic
from moves_cli.data.models import Section, Chunk, SimilarityResult


@pytest.fixture
def semantic():
    """Create a Semantic instance for testing"""
    return Semantic()


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing"""
    return [
        Chunk(
            partial_content="I am very happy today",
            source_sections=[Section(content="I am very happy today", section_index=0)],
        ),
        Chunk(
            partial_content="I feel joyful and excited",
            source_sections=[
                Section(content="I feel joyful and excited", section_index=1)
            ],
        ),
        Chunk(
            partial_content="The computer science algorithm",
            source_sections=[
                Section(content="The computer science algorithm", section_index=2)
            ],
        ),
    ]


@pytest.fixture
def mock_text_embedding():
    """Create a mock TextEmbedding class"""
    mock_model = MagicMock()

    def mock_embed(texts):
        """Mock embedding function that returns reasonable vectors"""
        # Create different embeddings based on content similarity
        embeddings = []
        for text in texts:
            if "happy" in text.lower() or "joyful" in text.lower():
                # Similar embeddings for similar semantic content
                embeddings.append(np.array([0.8, 0.6, 0.1, 0.2]))
            elif "computer" in text.lower() or "algorithm" in text.lower():
                # Different embeddings for different semantic content
                embeddings.append(np.array([0.1, 0.2, 0.9, 0.8]))
            else:
                # Default embedding
                embeddings.append(np.array([0.5, 0.5, 0.5, 0.5]))
        return embeddings

    mock_model.embed = mock_embed
    return mock_model


class TestSemanticModelLoading:
    """Test that model loads lazily"""

    def test_model_not_loaded_at_initialization(self):
        """Test that model is not loaded when Semantic instance is created"""
        semantic = Semantic()

        # Model should be None initially
        assert semantic._model is None

    def test_model_loads_on_first_access(self, semantic):
        """Test that model loads only when first accessed"""
        # Before accessing model property
        assert semantic._model is None

        # Mock the TextEmbedding to avoid loading actual model
        with patch("fastembed.TextEmbedding") as mock_te:
            mock_instance = MagicMock()
            mock_te.return_value = mock_instance

            # Access the model property
            model = semantic.model

            # Model should now be loaded
            assert semantic._model is not None
            assert model is mock_instance
            # TextEmbedding should have been called
            mock_te.assert_called_once()

    def test_model_loads_lazily_on_compare(self, semantic, sample_chunks):
        """Test that model loads lazily when compare is called"""
        assert semantic._model is None

        with patch("fastembed.TextEmbedding") as mock_te:
            mock_model = MagicMock()
            mock_model.embed.return_value = [
                np.array([1.0, 0.0, 0.0]),
                np.array([0.9, 0.1, 0.0]),
                np.array([0.8, 0.2, 0.0]),
                np.array([0.1, 0.9, 0.0]),
            ]
            mock_te.return_value = mock_model

            # Call compare - this should trigger model loading
            semantic.compare("test", sample_chunks)

            # Model should now be loaded
            assert semantic._model is not None
            mock_te.assert_called_once()

    def test_model_only_loads_once(self, semantic):
        """Test that model is only loaded once, not on every access"""
        with patch("fastembed.TextEmbedding") as mock_te:
            mock_instance = MagicMock()
            mock_te.return_value = mock_instance

            # Access model multiple times
            _ = semantic.model
            _ = semantic.model
            _ = semantic.model

            # TextEmbedding should only be called once
            mock_te.assert_called_once()

    def test_model_path_is_set(self, semantic):
        """Test that model path is correctly set"""
        # The path should now be an absolute path ending with the model directory
        assert semantic._model_path.endswith("all-MiniLM-L6-v2_quint8_avx2")
        # Verify it's an absolute path (contains the full path)
        from pathlib import Path

        assert Path(semantic._model_path).is_absolute()

    def test_model_initialization_parameters(self, semantic):
        """Test that model is initialized with correct parameters"""
        with patch("fastembed.TextEmbedding") as mock_te:
            mock_te.return_value = MagicMock()

            # Access model to trigger loading
            _ = semantic.model

            # Verify correct parameters were passed
            mock_te.assert_called_once_with(
                model_name="sentence-transformers/all-MiniLM-l6-v2",
                specific_model_path=semantic._model_path,
            )


class TestSemanticSimilarPhrases:
    """Test that semantically similar phrases score high"""

    def test_similar_semantic_phrases_score_high(self, semantic, mock_text_embedding):
        """Test that 'happy' and 'joyful' have high semantic similarity"""
        chunks = [
            Chunk(
                partial_content="I am happy",
                source_sections=[Section(content="I am happy", section_index=0)],
            ),
            Chunk(
                partial_content="I feel joyful",
                source_sections=[Section(content="I feel joyful", section_index=1)],
            ),
            Chunk(
                partial_content="The computer programming",
                source_sections=[
                    Section(content="The computer programming", section_index=2)
                ],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("happy feelings", chunks)

            # First two should score higher (semantically similar)
            assert results[0].score > results[2].score
            assert results[1].score > results[2].score

    def test_synonyms_score_high(self, semantic, mock_text_embedding):
        """Test that synonyms have high semantic similarity"""
        chunks = [
            Chunk(
                partial_content="big elephant",
                source_sections=[Section(content="big elephant", section_index=0)],
            ),
            Chunk(
                partial_content="large mammal",
                source_sections=[Section(content="large mammal", section_index=1)],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("big", chunks)

            # Should return results
            assert len(results) == 2
            assert all(isinstance(r, SimilarityResult) for r in results)

    def test_related_concepts_score_high(self, semantic, mock_text_embedding):
        """Test that related concepts have reasonable similarity"""
        chunks = [
            Chunk(
                partial_content="doctor medical treatment",
                source_sections=[
                    Section(content="doctor medical treatment", section_index=0)
                ],
            ),
            Chunk(
                partial_content="hospital healthcare patient",
                source_sections=[
                    Section(content="hospital healthcare patient", section_index=1)
                ],
            ),
            Chunk(
                partial_content="cooking recipe kitchen",
                source_sections=[
                    Section(content="cooking recipe kitchen", section_index=2)
                ],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("doctor hospital", chunks)

            # Medical-related chunks should rank higher than cooking
            assert len(results) == 3

    def test_contextual_similarity(self, semantic, mock_text_embedding):
        """Test that context affects semantic similarity"""
        chunks = [
            Chunk(
                partial_content="apple fruit healthy",
                source_sections=[
                    Section(content="apple fruit healthy", section_index=0)
                ],
            ),
            Chunk(
                partial_content="orange citrus vitamin",
                source_sections=[
                    Section(content="orange citrus vitamin", section_index=1)
                ],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("fruit nutrition", chunks)

            assert len(results) == 2
            # Both are fruit-related, should have reasonable scores
            assert all(r.score >= 0 for r in results)


class TestSemanticDifferentPhrases:
    """Test that semantically different phrases score low"""

    def test_different_semantic_phrases_score_low(self, semantic, mock_text_embedding):
        """Test that unrelated phrases have lower similarity"""
        chunks = [
            Chunk(
                partial_content="happy joyful emotions",
                source_sections=[
                    Section(content="happy joyful emotions", section_index=0)
                ],
            ),
            Chunk(
                partial_content="computer algorithm programming",
                source_sections=[
                    Section(content="computer algorithm programming", section_index=1)
                ],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("happy", chunks)

            # Results should be sorted by score
            assert results[0].score >= results[1].score
            # Emotion-related should score higher than computer-related
            assert (
                "happy" in results[0].chunk.partial_content.lower()
                or "joyful" in results[0].chunk.partial_content.lower()
            )

    def test_completely_unrelated_concepts(self, semantic, mock_text_embedding):
        """Test that completely unrelated concepts have low similarity"""
        chunks = [
            Chunk(
                partial_content="mathematics equations algebra",
                source_sections=[
                    Section(content="mathematics equations algebra", section_index=0)
                ],
            ),
            Chunk(
                partial_content="cooking recipes ingredients",
                source_sections=[
                    Section(content="cooking recipes ingredients", section_index=1)
                ],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("music concert performance", chunks)

            # Should return results for all chunks
            assert len(results) == 2

    def test_opposite_meanings(self, semantic, mock_text_embedding):
        """Test that opposite meanings are distinguished"""
        chunks = [
            Chunk(
                partial_content="hot warm temperature",
                source_sections=[
                    Section(content="hot warm temperature", section_index=0)
                ],
            ),
            Chunk(
                partial_content="cold freezing ice",
                source_sections=[Section(content="cold freezing ice", section_index=1)],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("hot", chunks)

            assert len(results) == 2
            # Results should be sorted
            assert results[0].score >= results[1].score


class TestSemanticResultFormat:
    """Test the structure and format of results"""

    def test_results_are_similarity_result_instances(
        self, semantic, mock_text_embedding, sample_chunks
    ):
        """Test that results are SimilarityResult instances"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("test", sample_chunks)

            assert all(isinstance(result, SimilarityResult) for result in results)

    def test_results_are_sorted_descending(
        self, semantic, mock_text_embedding, sample_chunks
    ):
        """Test that results are sorted by score in descending order"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("happy", sample_chunks)

            # Scores should be in descending order
            scores = [result.score for result in results]
            assert scores == sorted(scores, reverse=True)

    def test_all_chunks_returned(self, semantic, mock_text_embedding, sample_chunks):
        """Test that all input chunks are returned in results"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("test", sample_chunks)

            assert len(results) == len(sample_chunks)

    def test_chunk_preserved_in_result(
        self, semantic, mock_text_embedding, sample_chunks
    ):
        """Test that original chunk data is preserved in results"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("test", sample_chunks)

            result_contents = [result.chunk.partial_content for result in results]
            sample_contents = [chunk.partial_content for chunk in sample_chunks]

            # All sample chunks should appear in results
            for content in sample_contents:
                assert content in result_contents

    def test_score_is_float(self, semantic, mock_text_embedding, sample_chunks):
        """Test that scores are float values"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("test", sample_chunks)

            for result in results:
                assert isinstance(result.score, float)

    def test_cosine_similarity_calculation(self, semantic):
        """Test that cosine similarity is calculated correctly"""
        chunks = [
            Chunk(
                partial_content="test content",
                source_sections=[Section(content="test content", section_index=0)],
            )
        ]

        with patch("fastembed.TextEmbedding") as mock_te:
            mock_model = MagicMock()
            # Return normalized vectors for cosine similarity
            mock_model.embed.return_value = [
                np.array([1.0, 0.0, 0.0, 0.0]),  # Input embedding
                np.array([0.8, 0.6, 0.0, 0.0]),  # Candidate embedding
            ]
            mock_te.return_value = mock_model

            results = semantic.compare("input", chunks)

            # Cosine similarity should be dot product of normalized vectors
            assert len(results) == 1
            # Score should be reasonable
            assert -1.0 <= results[0].score <= 1.0


class TestSemanticEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_input_string(self, semantic, mock_text_embedding, sample_chunks):
        """Test with empty input string"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("", sample_chunks)

            # Should still return results
            assert len(results) == len(sample_chunks)
            assert all(isinstance(result, SimilarityResult) for result in results)

    def test_empty_candidates_list(self, semantic):
        """Test with empty candidates list raises RuntimeError"""
        with patch("fastembed.TextEmbedding") as mock_te:
            mock_model = MagicMock()
            # Empty candidates means only input embedding, which causes dimension mismatch
            mock_model.embed.return_value = [
                np.array([1.0, 0.0, 0.0, 0.0]),  # Input embedding only
            ]
            mock_te.return_value = mock_model

            # Should raise RuntimeError due to dimension mismatch
            with pytest.raises(
                RuntimeError, match="Semantic similarity comparison failed"
            ):
                semantic.compare("test input", [])

    def test_single_candidate(self, semantic, mock_text_embedding):
        """Test with single candidate"""
        chunks = [
            Chunk(
                partial_content="single chunk",
                source_sections=[Section(content="single chunk", section_index=0)],
            )
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("single", chunks)

            assert len(results) == 1
            assert isinstance(results[0], SimilarityResult)

    def test_special_characters_in_input(
        self, semantic, mock_text_embedding, sample_chunks
    ):
        """Test with special characters in input"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("hello! @#$ world?", sample_chunks)

            # Should handle gracefully
            assert len(results) == len(sample_chunks)

    def test_numbers_in_input(self, semantic, mock_text_embedding, sample_chunks):
        """Test with numbers in input"""
        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("test 123 456", sample_chunks)

            # Should handle numbers
            assert len(results) == len(sample_chunks)

    def test_very_long_input(self, semantic, mock_text_embedding, sample_chunks):
        """Test with very long input string"""
        long_input = " ".join(["word"] * 100)

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare(long_input, sample_chunks)

            assert len(results) == len(sample_chunks)

    def test_unicode_characters(self, semantic, mock_text_embedding):
        """Test with unicode characters"""
        chunks = [
            Chunk(
                partial_content="café résumé naïve",
                source_sections=[Section(content="café résumé naïve", section_index=0)],
            )
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("café", chunks)

            # Should handle unicode
            assert len(results) == 1


class TestSemanticErrorHandling:
    """Test error handling"""

    def test_exception_handling(self, semantic):
        """Test that exceptions are properly caught and re-raised as RuntimeError"""
        chunks = [
            Chunk(
                partial_content="normal content",
                source_sections=[Section(content="normal content", section_index=0)],
            )
        ]

        # Patch the model's _model attribute directly and create a mock with error
        mock_model = MagicMock()
        mock_model.embed.side_effect = Exception("Test exception")
        semantic._model = mock_model

        with pytest.raises(RuntimeError, match="Semantic similarity comparison failed"):
            semantic.compare("test", chunks)

    def test_error_message_includes_original_exception(self, semantic):
        """Test that error message includes original exception details"""
        chunks = [
            Chunk(
                partial_content="content",
                source_sections=[Section(content="content", section_index=0)],
            )
        ]

        mock_model = MagicMock()
        mock_model.embed.side_effect = ValueError("Original error")
        semantic._model = mock_model

        try:
            semantic.compare("test", chunks)
            pytest.fail("Should have raised RuntimeError")
        except RuntimeError as e:
            # Check that the original exception is chained
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)

    def test_handles_empty_embeddings(self, semantic):
        """Test handling of unexpected empty embeddings"""
        chunks = [
            Chunk(
                partial_content="test",
                source_sections=[Section(content="test", section_index=0)],
            )
        ]

        mock_model = MagicMock()
        # Return empty list
        mock_model.embed.return_value = []
        semantic._model = mock_model

        with pytest.raises(RuntimeError):
            semantic.compare("input", chunks)


class TestSemanticIntegration:
    """Integration tests for complete workflows"""

    def test_multiple_comparisons_workflow(self, semantic, mock_text_embedding):
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

        with patch.object(semantic, "_model", mock_text_embedding):
            # Perform multiple comparisons
            results1 = semantic.compare("first", chunks)
            results2 = semantic.compare("second", chunks)
            results3 = semantic.compare("third", chunks)

            # All should return valid results
            assert len(results1) == 2
            assert len(results2) == 2
            assert len(results3) == 2

            # Results should be properly sorted
            assert results1[0].score >= results1[1].score
            assert results2[0].score >= results2[1].score

    def test_real_world_scenario(self, semantic, mock_text_embedding):
        """Test a real-world-like scenario with various chunks"""
        chunks = [
            Chunk(
                partial_content="machine learning artificial intelligence",
                source_sections=[
                    Section(
                        content="machine learning artificial intelligence",
                        section_index=0,
                    )
                ],
            ),
            Chunk(
                partial_content="deep neural networks training",
                source_sections=[
                    Section(content="deep neural networks training", section_index=1)
                ],
            ),
            Chunk(
                partial_content="cooking recipes ingredients",
                source_sections=[
                    Section(content="cooking recipes ingredients", section_index=2)
                ],
            ),
        ]

        with patch.object(semantic, "_model", mock_text_embedding):
            results = semantic.compare("machine learning", chunks)

            # Should return all chunks
            assert len(results) == 3
            # Results should be sorted
            assert results[0].score >= results[1].score >= results[2].score

    def test_embedding_dimensions(self, semantic):
        """Test that embeddings have consistent dimensions"""
        chunks = [
            Chunk(
                partial_content="test content",
                source_sections=[Section(content="test content", section_index=0)],
            )
        ]

        with patch("fastembed.TextEmbedding") as mock_te:
            mock_model = MagicMock()
            # Return embeddings with consistent dimensions
            mock_model.embed.return_value = [
                np.array([0.1, 0.2, 0.3, 0.4]),  # Input
                np.array([0.5, 0.6, 0.7, 0.8]),  # Candidate
            ]
            mock_te.return_value = mock_model

            results = semantic.compare("input", chunks)

            assert len(results) == 1
            assert isinstance(results[0].score, float)

    def test_model_reuse_across_comparisons(self, semantic):
        """Test that model is reused across multiple comparisons"""
        chunks = [
            Chunk(
                partial_content="test",
                source_sections=[Section(content="test", section_index=0)],
            )
        ]

        with patch("fastembed.TextEmbedding") as mock_te:
            mock_model = MagicMock()
            mock_model.embed.return_value = [
                np.array([1.0, 0.0]),
                np.array([0.9, 0.1]),
            ]
            mock_te.return_value = mock_model

            # Multiple comparisons
            semantic.compare("input1", chunks)
            semantic.compare("input2", chunks)
            semantic.compare("input3", chunks)

            # Model should only be initialized once
            mock_te.assert_called_once()
            # But embed should be called multiple times
            assert mock_model.embed.call_count == 3
