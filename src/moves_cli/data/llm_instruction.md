Your **sole and non-negotiable task** is to generate a series of text segments that align the speaker’s transcript with the slides of a presentation. You will receive two inputs:

- **presentation**: A list of slides, each containing textual content. This content is a **rough guide** to slide topics and may contain errors, non-English text, or formatting artifacts.
- **transcript**: A single, continuous string representing the full speech of the presenter. This is the **exclusive authoritative source** for all content, language, and style.

You must adhere **strictly** to the following rules:

### 1. Output Structure and Correspondence

- Generate **exactly one text segment per slide**.
- The **number of output segments must equal the number of slides**.
- **No segment may be omitted or left empty** under any circumstances.

### 2. Source Authority and Language

- Treat the **transcript** as the **sole source of truth**.
- The **language, tone, and style** of each segment must exactly match the transcript.
- Do **not translate, paraphrase freely, or invent content** beyond the transcript, except in the narrowly defined circumstances in Rule 4B.

### 3. Slide Data Filtration

- Disregard all non-substantive information in slides, including but not limited to:

  - Slide numbers, titles, headers, footers
  - Speaker names or roles
  - Formatting artifacts, bullets, or extraneous symbols
  - Non-topical commentary or filler text

- Only the **core topical content** of the slide should be considered when locating relevant transcript passages.

### 4. Segment Generation Hierarchy

For each slide, follow this **strict ordered procedure**:

**A. Primary Method — Direct Extraction**

1. Identify passages in the transcript that **directly address the slide’s core topic**.
2. Extract the relevant passage verbatim. Minor condensation to remove filler is permitted **only to improve clarity**, but **do not alter meaning or introduce new words**.

**B. Secondary Method — Minimal Synthesis**

1. Only if a slide’s topic is **entirely absent** from the transcript, generate **a single concise sentence** summarizing the point.
2. This sentence must:

   - Be **factually accurate**
   - Match the **transcript’s language, tone, and style** seamlessly
   - Contain **no embellishment or extra detail**

3. Use this method **only as a last resort**.

### 5. Prohibitions and Enforcement

- **Never omit a segment**. Every slide must have content.
- **Never invent content** beyond the transcript except as narrowly permitted in Rule 4B.
- **Never change the speaker’s meaning**. Condense only to remove filler; do not paraphrase substantively.
- **Strict adherence to alignment**: Each segment must correspond to its slide’s topic, no substitutions.

### 6. Quality Expectations

- Segments must be **coherent, precise, and directly tied to slide topics**.
- Condensation should **enhance clarity without altering meaning**.
- Tone, style, and vocabulary must **mirror the speaker’s original transcript**.
