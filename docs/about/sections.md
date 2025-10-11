# Section Production

Section production is the AI-powered core of the `moves` offline data preparation pipeline. Orchestrated by the `section_producer`, this process transforms an unstructured transcript into a list of "Sections," where each section is semantically aligned with a single slide of a presentation. This structured data is the foundation upon which the entire real-time navigation system is built.

## Detailed Process Flow

The production process is initiated via the `moves speaker process` command and proceeds as follows:

1.  **Text Extraction from PDFs:**
    The `PyMuPDF` library is used for its high-fidelity text extraction capabilities.

    - **Presentation:** Text is extracted page-by-page, preserving the inherent structure of the slides. This collection of per-page text serves as the topical guide for the LLM.
    - **Transcript:** The entire transcript is extracted as one continuous string, representing the complete narrative that needs to be segmented.

2.  **Structured LLM Invocation:**
    `moves` employs a sophisticated stack for interacting with LLMs to ensure reliable and predictable results.

    - **`litellm`:** Acts as a universal translation layer, allowing `moves` to communicate with various LLM APIs (OpenAI, Gemini, etc.) using a single, consistent interface.
    - **`instructor`:** This library works in tandem with Pydantic to enforce a specific output schema on the LLM's response. The `section_producer` defines a `SectionsOutputModel` Pydantic model that specifies the exact structure, data types, and constraints (e.g., the number of sections must match the number of slides) of the expected JSON output. By passing this model to `instructor`, the system can automatically validate and parse the LLM's JSON response, retrying the call if the output is malformed.

3.  **Prompt Engineering and the Alignment Task:**
    The LLM is guided by a carefully crafted system prompt located in `src/data/llm_instruction.md`. This prompt defines a clear set of rules and constraints for the semantic alignment task:

    - **Primary Objective:** To generate one text segment for each slide provided. The output must be an exact one-to-one mapping.
    - **Source Authority:** The transcript is the definitive source for all content and language. The LLM must extract passages directly from it.
    - **Semantic Matching:** The model must ignore superficial elements from the presentation slides (like slide numbers, templates, or speaker notes) and focus on matching the core topical meaning of each slide to the relevant part of the transcript.
    - **Hierarchical Content Generation:** The prompt specifies a strict procedure. The primary method is direct extraction from the transcript. Only if a slide's topic is verifiably absent from the entire transcript is the model permitted to synthesize a single, concise sentence in the speaker's style. This fallback ensures no section is left empty.

4.  **Serialization and Persistence:**
    Upon receiving the validated, structured response from the LLM, the `section_producer` converts the data into a list of `Section` objects. This list is then serialized to `sections.json` and saved in the speaker's dedicated data directory, concluding the processing stage and marking the speaker as "Ready" for a presentation.
