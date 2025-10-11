# Chunk Production

Chunk production is a critical offline process that deconstructs the `Section` data into small, overlapping text segments known as "Chunks." This transformation is fundamental to the system's real-time performance and accuracy, as it creates a data structure optimized for rapid and resilient similarity matching. This process is orchestrated by the `chunk_producer`.

## The Rationale Behind Chunks

Matching live speech against entire `Section` paragraphs is computationally inefficient and highly susceptible to failure if the speaker deviates from the script. Chunks address this by providing:

- **Granularity and Overlap:** By breaking content into small, overlapping phrases (e.g., 12 words), the system can match short spoken phrases with high confidence, even if they are delivered out of order or with ad-libbed connecting words. The overlap ensures that a phrase is represented in multiple chunks, increasing the probability of a successful match.
- **Performance:** The real-time similarity engine only needs to compare the live speech against short strings, which is orders of magnitude faster than performing vector or phonetic analysis on entire paragraphs.

## The `generate_chunks` Process

The `generate_chunks` function employs a sliding window algorithm to create a comprehensive list of all possible chunks from the entire presentation script.

1.  **Word Corpus Construction:** The process begins by tokenizing the content of all `Section` objects into a single, ordered list. This is not merely a list of strings; it is a list of tuples, where each tuple contains the word and a reference to its source `Section` object: `(word, source_section)`. This preserves the crucial metadata linking every word back to its corresponding slide.
2.  **Sliding Window Iteration:** A window of a fixed `window_size` (defaulting to 12 words) slides across the word corpus. The iteration proceeds one word at a time, from the first word up to the `(n - window_size)`-th word, where `n` is the total number of words in the corpus.
3.  **Chunk Object Instantiation:** For each position of the window, a new `Chunk` object is created:
    - **`partial_content`**: The word elements from the current window slice are joined into a single string. This string is then passed through the `text_normalizer` to ensure its format is identical to the normalized STT output during the live session.
    - **`source_sections`**: The unique `Section` objects associated with the words in the window are collected. This list is then sorted by `section_index` to maintain a chronologically accurate record of the chunk's origins. A single chunk can span multiple sections if its window crosses a section boundary.

## The `get_candidate_chunks` Selection Logic

To optimize real-time performance, the `SimilarityCalculator` does not search through all generated chunks. Instead, the `get_candidate_chunks` function provides a small, contextually relevant subset of chunks based on the current slide.

1.  **Candidate Window Definition:** Based on the `section_index` of the current slide (`idx`), a "look-ahead/look-behind" window is defined, spanning from two sections before to three sections after the current one (`idx - 2` to `idx + 3`). This window anticipates both forward navigation and the possibility of the speaker needing to briefly refer back.
2.  **Primary Filtering:** The first filter selects all chunks for which **every one** of its `source_sections` has an index that falls within this defined candidate window. This drastically reduces the search space.
3.  **Edge Case Refinement:** A second, more subtle filter is applied to refine the candidate set. It excludes any chunk that meets two conditions simultaneously: (1) it is sourced from only a single section, and (2) that single section is at the absolute edge of the candidate window (i.e., at index `idx - 2` or `idx + 3`). This heuristic prevents the system from prematurely matching with content that is still two or three slides away, prioritizing chunks that are more central to the current topic or serve as a direct bridge to the immediately adjacent slides.
