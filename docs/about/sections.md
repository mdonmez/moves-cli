# Section Production: LLM-Powered Transcript Alignment

## Overview

Section production is the AI-powered foundation of the `moves` data preparation pipeline. The `section_producer` transforms an unstructured transcript into a structured list of "Sections," where each section is semantically aligned with a single presentation slide. This structured data forms the basis for all subsequent real-time navigation.

## Process Architecture

The production process is initiated via `moves speaker process` and executes through four distinct stages:

### Stage 1: PDF Text Extraction

**Technology:** `PyMuPDF` library for high-fidelity text extraction

**Presentation Extraction:**
- **Method:** Page-by-page extraction preserving slide structure
- **Output:** Collection of per-page text strings
- **Purpose:** Provides topical guidance for the LLM
- **Processing:** Whitespace normalization (multi-space → single space)
- **Format:** Markdown with slide headers (`# Slide Page 0`, `# Slide Page 1`, etc.)

**Transcript Extraction:**
- **Method:** Complete document extraction as continuous text
- **Output:** Single unified string representing full narrative
- **Purpose:** Source material for segmentation
- **Processing:** Whitespace consolidation for consistency
- **Format:** Plain text with normalized spacing

**Error Handling:**
- Wrapped in try-except for robust error reporting
- Raises `RuntimeError` with detailed context on failure
- Includes file path and extraction type in error messages

### Stage 2: LLM Integration Stack

**Technology Stack:**

**`litellm`** - Universal LLM API Translation Layer
- Provides consistent interface across multiple LLM providers
- Abstracts provider-specific API differences
- Supports OpenAI, Google Gemini, Anthropic, and 100+ others
- Enables model switching without code changes

**`instructor`** - Structured Output Enforcement
- Works with Pydantic to enforce output schemas
- Automatically validates LLM responses against defined models
- Implements retry logic for malformed outputs
- Guarantees type-safe, predictable results

**`Pydantic`** - Data Validation Framework
- Defines `SectionsOutputModel` with strict constraints
- Validates data types, ranges, and structural requirements
- Ensures one section per slide (enforced via min/max items)
- Provides automatic JSON parsing and validation

### Output Model Structure

```python
class SectionsOutputModel(BaseModel):
    class SectionItem(BaseModel):
        section_index: int = Field(..., ge=0, description="Index starting from 0")
        content: str = Field(..., description="Content of the section")
    
    sections: list[SectionItem] = Field(
        ...,
        description="List of section items, one for each slide",
        min_items=len(presentation_slides),
        max_items=len(presentation_slides),
    )
```

**Validation Rules:**
- `section_index`: Must be non-negative integer (≥ 0)
- `content`: Required string field
- `sections`: List length must exactly match slide count
- Automatic retry if any constraint is violated

### Stage 3: Prompt Engineering and Alignment Task

**System Prompt Location:** `src/moves_cli/data/llm_instruction.md`

The LLM receives a carefully engineered system prompt defining the semantic alignment task with explicit rules and constraints:

#### Primary Objective
Generate exactly one text segment for each presentation slide, maintaining a one-to-one mapping between output sections and input slides.

#### Core Alignment Rules

**1. Source Authority**
- Transcript is the definitive source for all content
- Extract passages directly from the transcript
- Preserve the speaker's language and phrasing
- Do not synthesize content from slide text alone

**2. Semantic Matching**
- Focus on core topical meaning of each slide
- Ignore superficial elements (slide numbers, templates, footers)
- Disregard speaker notes and metadata
- Match slide concepts to corresponding transcript content

**3. Content Generation Hierarchy**

**Primary Method: Direct Extraction**
- Locate relevant transcript passage for each slide topic
- Extract the exact text discussing that topic
- Maintain chronological flow when possible

**Fallback Method: Minimal Synthesis** (when topic is absent from transcript)
- Create a single, concise sentence
- Match the speaker's established style and tone
- State the slide topic directly
- Minimize invented content

**4. Output Constraints**
- Number of sections must exactly equal number of slides
- Each section must have valid index and content
- Sections must be in chronological order (0, 1, 2, ...)
- No sections can be empty or null

#### LLM Call Parameters

**Model:** User-configured via `moves settings set model`

**Temperature:** 0.2 (low temperature for consistent, focused output)

**Messages:**
```python
[
    {"role": "system", "content": llm_instruction.md},
    {"role": "user", "content": "Presentation: ...\nTranscript: ..."}
]
```

**Response Format:** Structured JSON validated by `SectionsOutputModel`

### Stage 4: Serialization and Persistence

**Process Flow:**

1. **Response Validation**
   - `instructor` validates LLM response against `SectionsOutputModel`
   - Automatically retries if validation fails
   - Ensures structural correctness and constraint compliance

2. **Data Transformation**
   - Extract `content` field from each `SectionItem`
   - Preserve `section_index` ordering
   - Convert to list of `Section` dataclass objects

3. **File Serialization**
   - Serialize `Section` list to JSON format
   - Write to `sections.json` in speaker directory
   - Location: `~/.moves/speakers/<speaker_id>/sections.json`

4. **Status Update**
   - Presence of `sections.json` marks speaker as "Ready"
   - Speaker can now be used for presentation control
   - File serves as input for chunk generation

**Output Format Example:**
```json
[
    {
        "content": "Welcome everyone to today's presentation...",
        "section_index": 0
    },
    {
        "content": "Let's start by discussing the main features...",
        "section_index": 1
    },
    ...
]
```

## Error Handling

**PDF Extraction Errors:**
- Catch exceptions during `PyMuPDF` operations
- Raise `RuntimeError` with file path and extraction type
- Provide actionable error messages to user

**LLM Call Errors:**
- Catch API errors, timeouts, rate limits
- Raise `RuntimeError` with detailed context
- Include model name and error type in message

**Validation Errors:**
- `instructor` handles malformed responses automatically
- Retries with adjusted parameters
- Eventually fails with clear error if retry limit exceeded

## Quality Assurance

**Output Verification:**
- Section count matches slide count (enforced by Pydantic)
- All sections have valid indices (0 to n-1)
- All sections have non-empty content
- Chronological ordering is maintained

**Re-processing Support:**
- Process is idempotent (can run multiple times)
- Overwrites existing `sections.json`
- Useful when source files are updated
- Useful when changing LLM models or settings
