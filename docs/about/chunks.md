# Chunk Production System

## Overview

Chunk production is a critical offline process that transforms `Section` data into small, overlapping text segments called "Chunks." This transformation creates a data structure optimized for rapid and resilient real-time similarity matching, forming the foundation for accurate voice-driven slide navigation.

## Design Rationale

### Why Chunks Are Essential

Matching live speech against entire `Section` paragraphs presents two fundamental challenges:

1. **Computational Inefficiency:** Comparing long text segments is slow and resource-intensive
2. **Brittleness:** Minor deviations from the script cause matching failures

Chunks solve both problems through:

**Granularity and Overlap**
- Small 12-word segments enable precise matching of short spoken phrases
- Overlapping windows ensure phrases appear in multiple chunks
- Redundancy increases match probability even with ad-libbed content or out-of-order delivery

**Performance Optimization**
- Short string comparisons are orders of magnitude faster than paragraph analysis
- Vector and phonetic operations on 12-word segments execute in real-time
- Enables continuous processing without latency

**Resilience**
- Tolerates speaker variations, pauses, and connecting words
- Maintains accuracy when speakers deviate from the script
- Robust against partial phrase matches

## The `generate_chunks` Algorithm

The `generate_chunks` function implements a sliding window algorithm to create a comprehensive set of chunks from all sections in a presentation.

### Implementation Steps

**1. Word Corpus Construction**

The algorithm begins by tokenizing all `Section` content into a single ordered list. Each element is a tuple preserving essential metadata:

```python
[(word, source_section), (word, source_section), ...]
```

This structure maintains the link between every word and its originating section, critical for tracing matches back to specific slides.

**2. Sliding Window Iteration**

A fixed-size window (default: 12 words) slides across the word corpus one word at a time:
- **Start position:** 0
- **End position:** `(total_words - window_size)`
- **Step size:** 1 word (creates maximum overlap)

**3. Chunk Object Creation**

For each window position, a new `Chunk` object is instantiated with two key properties:

**`partial_content`** (str)
- Words from the current window are joined into a single string
- Passed through `text_normalizer` for canonical formatting
- Ensures identical format to real-time STT output
- Example: "the quick brown fox jumps over the lazy dog cat mouse"

**`source_sections`** (list[Section])
- Collects unique `Section` objects associated with window words
- Sorted by `section_index` for chronological accuracy
- Spans multiple sections when window crosses section boundaries
- Enables precise slide navigation from chunk matches

### Algorithm Characteristics

- **Total chunks:** `(total_words - window_size + 1)`
- **Overlap:** 11 words between consecutive chunks
- **Coverage:** Every 12-word phrase in the presentation appears at least once
- **Cross-section chunks:** Enable smooth transitions between slides

## Candidate Chunk Selection

To optimize real-time performance, the `SimilarityCalculator` evaluates only a contextually relevant subset of chunks. The `get_candidate_chunks` function implements intelligent filtering based on the current slide position.

### Selection Strategy

**1. Define Candidate Window**

Based on the current slide's `section_index` (idx), establish a look-ahead/look-behind range:

```
Window: [idx - 2, idx + 3]
```

This asymmetric window:
- Looks back 2 slides (handles speaker backtracking or recap)
- Looks ahead 3 slides (anticipates forward progression)
- Balances context while maintaining performance

**2. Primary Filtering**

Select chunks where **all** source sections fall within the candidate window:

```python
all(start <= section.section_index <= end for section in chunk.source_sections)
```

This dramatically reduces the search space while ensuring relevant chunks are included.

**3. Edge Case Refinement**

Apply a second filter to exclude peripheral chunks that could cause premature matching:

**Exclusion criteria:**
- Chunk sourced from exactly one section, AND
- That section is at the absolute window edge (idx - 2 or idx + 3)

**Rationale:**
- Prevents matching content that's 2-3 slides away
- Prioritizes chunks central to current context
- Favors chunks spanning multiple sections (natural transitions)

### Selection Benefits

- **Reduced search space:** Typically 10-20% of total chunks
- **Context awareness:** Focuses on relevant presentation area
- **Transition support:** Includes chunks bridging adjacent slides
- **Performance:** Enables real-time similarity calculations
- **Accuracy:** Prevents false matches from distant content

### Example Scenario

Current slide: 10 (idx = 10)
- Candidate window: [8, 13]
- Included: Chunks from sections 8-13 and their combinations
- Excluded: Single-section chunks from sections 8 and 13
- Focus: Multi-section chunks and chunks from sections 9-12
