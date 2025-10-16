# Similarity Calculation Engine

## Overview

The `SimilarityCalculator` is the analytical core of the real-time control engine, responsible for determining the degree of similarity between live speech and pre-processed presentation content. It employs a hybrid scoring model combining semantic and phonetic analysis to achieve both accuracy and robustness against speech variations.

## Hybrid Analysis Architecture

The dual-pronged approach captures both meaning and pronunciation, providing comprehensive similarity assessment superior to either method alone.

### Component 1: Semantic Similarity

**Purpose:** Assess contextual and thematic meaning of text

**Technology Stack:**
- **Library:** `fastembed` - Fast, efficient embedding generation
- **Model:** `sentence-transformers/all-MiniLM-l6-v2`
  - Optimized for sentence-level embeddings
  - Runs entirely offline (no API calls)
  - Fast inference suitable for real-time use
  - 384-dimensional embeddings

**Process Flow:**

1. **Embedding Generation**
   - Convert live spoken phrase to vector embedding
   - Convert each candidate chunk to vector embedding
   - Embeddings capture semantic meaning in high-dimensional space

2. **Similarity Calculation**
   - Compute cosine similarity between phrase and chunk vectors
   - Formula: `cos(θ) = (A · B) / (||A|| × ||B||)`
   - Result: Similarity score in range [0.0, 1.0]
   - Score of 1.0 indicates identical semantic meaning

3. **Semantic Advantages**
   - Captures synonyms and paraphrasing
   - Understands contextual word relationships
   - Robust to word order variations
   - Language-model informed understanding

**Implementation Detail:**
```python
# Semantic similarity using fastembed
embeddings_input = self.embedding_model.embed([input_str])
embeddings_chunks = self.embedding_model.embed([chunk.partial_content for chunk in candidates])
cosine_similarities = compute_cosine_similarity(embeddings_input, embeddings_chunks)
```

### Component 2: Phonetic Similarity

**Purpose:** Analyze phonetic structure to handle pronunciation variations

**Technology Stack:**
- **Phonetic Encoding:** `jellyfish` - Metaphone algorithm implementation
- **Fuzzy Matching:** `rapidfuzz` - High-speed string similarity
- **Caching:** `@lru_cache` decorator - Performance optimization

**Process Flow:**

1. **Phonetic Encoding (Metaphone)**
   - Convert input text to phonetic representation
   - Convert chunk text to phonetic representation
   - Algorithm focuses on pronunciation, not spelling
   - Example transformations:
     - "phonetics" → "FNTKS"
     - "fonetics" → "FNTKS" (same encoding)
     - "night" → "NT"
     - "knight" → "NT" (same encoding)

2. **Fuzzy String Matching**
   - Compare phonetic keys using Levenshtein distance
   - Calculate minimum edits needed to transform one key to another
   - Normalize result to [0.0, 1.0] scale via `rapidfuzz.ratio()`
   - Higher score indicates more similar pronunciation

3. **Performance Optimization**
   - Phonetic codes cached using `@lru_cache`
   - Similarity ratios cached for recent comparisons
   - Prevents redundant computation for repeated phrases
   - Significant performance gain in real-time scenarios

**Phonetic Advantages:**
- Resilient to homophones ("their" vs. "there")
- Tolerates minor mispronunciations
- Compensates for STT transcription errors
- Handles spelling variations
- Robust to accent-related variations

**Implementation Detail:**
```python
# Phonetic similarity using jellyfish + rapidfuzz
@lru_cache(maxsize=1000)
def get_metaphone(text: str) -> str:
    return jellyfish.metaphone(text)

@lru_cache(maxsize=10000)
def get_phonetic_similarity(text1: str, text2: str) -> float:
    code1 = get_metaphone(text1)
    code2 = get_metaphone(text2)
    return rapidfuzz.fuzz.ratio(code1, code2) / 100.0
```

## Score Aggregation and Weighting

The `SimilarityCalculator` orchestrates both similarity units and intelligently combines their results through a three-step process.

### Step 1: Independent Score Normalization

**Purpose:** Make semantic and phonetic scores comparable on equal footing

**The `_normalize_scores` Method:**

1. **Confidence Filtering**
   - Remove scores below 0.5 confidence threshold
   - Eliminates clearly poor matches
   - Prevents low-quality results from skewing normalization

2. **Min-Max Scaling**
   - Identify minimum and maximum values among valid scores
   - Apply transformation: `normalized = (score - min) / (max - min)`
   - Maps scores to [0.0, 1.0] range within candidate set
   - Score of 1.0 represents best match in current context
   - Score of 0.0 assigned to filtered-out low-confidence matches

3. **Edge Case Handling**
   - **All scores below threshold:** All normalized to 0.0
   - **All scores equal:** Valid scores normalized to 1.0, invalid to 0.0
   - **Empty candidate set:** Returns empty dictionary

**Why Normalization is Critical:**
- Semantic and phonetic scores have different statistical distributions
- Raw scores are not directly comparable
- Normalization ensures balanced contribution from both methods
- Context-aware: normalization is relative to current candidate pool

**Example:**
```
Raw semantic scores: [0.72, 0.85, 0.91, 0.45, 0.63]
After filtering (≥0.5): [0.72, 0.85, 0.91, 0.63]
Min: 0.63, Max: 0.91
Normalized: [0.32, 0.79, 1.0, 0.0, 0.0]
```
### Step 2: Weighted Score Combination

**Purpose:** Combine normalized semantic and phonetic scores into final similarity score

**Weighting Formula:**
```
final_score = (semantic_weight × semantic_norm) + (phonetic_weight × phonetic_norm)
```

**Default Configuration:**
- `semantic_weight`: 0.6 (60%)
- `phonetic_weight`: 0.4 (40%)

**Rationale for 60/40 Split:**
- Semantic similarity captures overall meaning and context
- Phonetic similarity provides error correction and robustness
- Meaning is prioritized but pronunciation variations are accommodated
- Empirically determined balance for presentation content

**Configurability:**
Weights can be adjusted via `SimilarityCalculator` constructor:
```python
calculator = SimilarityCalculator(
    semantic_weight=0.7,  # Prioritize meaning more
    phonetic_weight=0.3   # Reduce phonetic influence
)
```

**Weight Constraints:**
- Both weights should be non-negative
- Typically sum to 1.0 (not strictly enforced)
- Extreme values (0 or 1) disable one component entirely

### Step 3: Final Ranking and Selection

**Process:**

1. **Result Object Creation**
   - Create `SimilarityResult` for each candidate chunk
   - Pair chunk with its final weighted score
   - Encapsulates all necessary navigation information

2. **Sorting**
   - Sort results by final score in descending order
   - Highest score appears first in list
   - Deterministic ordering for equal scores (implementation-dependent)

3. **Navigation Decision**
   - `PresentationController` selects top result (highest score)
   - Extracts target slide from chunk's `source_sections`
   - Calculates navigation delta from current slide
   - Executes keyboard commands to reach target slide

**Output Format:**
```python
[
    SimilarityResult(chunk=chunk_A, score=0.87),  # Best match
    SimilarityResult(chunk=chunk_B, score=0.73),
    SimilarityResult(chunk=chunk_C, score=0.61),
    ...
]
```

## Algorithm Summary

**Complete Similarity Calculation Pipeline:**

1. **Input:** Live spoken phrase (12 normalized words)
2. **Candidate Selection:** `get_candidate_chunks()` filters ~20% of total chunks
3. **Semantic Analysis:** Generate embeddings, calculate cosine similarities
4. **Phonetic Analysis:** Generate Metaphone codes, calculate fuzzy ratios
5. **Normalization:** Apply min-max scaling to both score sets independently
6. **Weighting:** Combine normalized scores (60% semantic + 40% phonetic)
7. **Ranking:** Sort by final weighted score
8. **Output:** Ordered list of `SimilarityResult` objects

**Performance Characteristics:**
- **Latency:** < 100ms for typical candidate set (~50-100 chunks)
- **Accuracy:** High precision with balanced semantic/phonetic approach
- **Robustness:** Handles speech variations, STT errors, paraphrasing
- **Scalability:** Candidate filtering enables constant-time performance
