# Similarity Calculations

The `SimilarityCalculator` is the analytical core of the `moves` real-time engine. It is responsible for determining the degree of similarity between a speaker's live utterance and the pre-processed presentation text. To achieve high accuracy and robustness against the nuances of live speech, it employs a hybrid model that integrates semantic and phonetic analysis, combining their outputs into a single, weighted score.

## Hybrid Analysis Model

This dual-pronged approach is designed to capture both the meaning and the sound of the spoken words, providing a more comprehensive measure of similarity than either method could achieve alone.

### 1. Semantic Similarity

This unit assesses the contextual and thematic meaning of the text.

- **Technology:** It leverages the `fastembed` library with the `sentence-transformers/all-MiniLM-l6-v2` embedding model. This model is highly efficient and runs locally, making it ideal for real-time applications.
- **Process:** The live spoken phrase and each candidate `Chunk` are passed to the model, which converts them into high-dimensional numerical vectors (embeddings). The semantic similarity is then quantified by calculating the cosine similarity between the vector of the spoken phrase and the vector of each chunk. This metric effectively measures the angle between the vectors in multi-dimensional space; a smaller angle (cosine similarity closer to 1.0) indicates that the texts are semantically closer.

### 2. Phonetic Similarity

This unit analyzes the phonetic structure of the text, providing resilience to mispronunciations, homophones (e.g., "there" vs. "their"), and errors from the speech-to-text engine.

- **Technology:** It combines `jellyfish` for phonetic encoding and `rapidfuzz` for high-speed string comparison.
- **Process:**
  1.  **Phonetic Encoding:** The Metaphone algorithm from `jellyfish` is applied to both the input string and the candidate chunk's content. This algorithm generates a phonetic key that represents how the text sounds (e.g., "phonetics" -> "FNTKS"). This step abstracts away from the literal spelling.
  2.  **Fuzzy Matching:** The `rapidfuzz.ratio` function is then used to compare the two generated phonetic keys. This function calculates a similarity score based on the Levenshtein distance, measuring the number of edits required to make the strings identical. The result is normalized to a 0.0-1.0 scale.
  3.  **Caching:** Both the phonetic codes and the fuzz ratios are cached using `@lru_cache` to avoid re-computation for recently heard phrases, further optimizing performance.

## Score Aggregation and Weighted Combination

The `SimilarityCalculator` orchestrates these two units and intelligently combines their results.

1.  **Score Normalization:** The raw scores from the semantic and phonetic analyses are not directly comparable due to their different scales and statistical distributions. The `_normalize_scores` method is applied to each set of scores independently. It first filters out any scores below a minimum confidence threshold of 0.5. Then, it applies a min-max scaling to the remaining valid scores, mapping them to a new 0.0-1.0 range where 1.0 represents the best match _within that candidate set_. This prevents low-quality matches from skewing the final result and ensures both metrics contribute on a level playing field.
2.  **Weighted Sum:** The final similarity score for each chunk is calculated as a weighted sum of its normalized semantic and phonetic scores. These weights (`semantic_weight` and `phonetic_weight`) are configurable and default to 0.6 and 0.4, respectively. This allows the system's behavior to be fine-tuned, prioritizing either semantic meaning or phonetic accuracy as needed.
3.  **Final Ranking:** The `SimilarityCalculator` returns a list of `SimilarityResult` objects, sorted in descending order of their final weighted score. This allows the `PresentationController` to deterministically select the single best-matching chunk and proceed with navigation.
