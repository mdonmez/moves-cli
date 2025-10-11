# Streaming Speech-to-Text

The real-time responsiveness of `moves` is powered by a low-latency, offline Streaming Speech-to-Text (STT) engine implemented within the `PresentationController`. This engine is engineered to continuously transcribe a speaker's voice with minimal delay, providing the constant stream of text necessary for the similarity matching algorithm.

## Core Technology and Configuration

- **STT Library:** `moves` uses `sherpa-onnx`, a high-performance speech recognition toolkit that leverages ONNX Runtime for efficient, cross-platform execution of neural network models. Its offline nature is a key design choice, eliminating network latency and ensuring user privacy.
- **Acoustic Model:** The system is packaged with a pre-trained Nemo transducer model, which is specifically designed for streaming applications. Transducer models are advantageous because they can emit recognition results incrementally as audio is received, rather than waiting for pauses in speech.
- **Decoding Method:** The recognizer is configured to use `"greedy_search"` for decoding. This method selects the single most probable token at each step of the recognition process. While more complex methods like beam search can sometimes yield higher accuracy, greedy search provides the lowest possible latency, which is the paramount concern for a real-time control application.

## Multi-Threaded Audio Processing Pipeline

To ensure that audio capture, STT processing, and presentation navigation do not interfere with one another, the system uses a multi-threaded architecture.

1.  **Audio Capture (Main Thread):** The `sounddevice` library initiates an input stream in the main application thread. This is a blocking operation that continuously captures audio from the default microphone in 100-millisecond frames at a 16,000 Hz sample rate. A callback function is registered with the stream.

2.  **Asynchronous Buffering:** The audio capture callback's sole responsibility is to place the incoming audio frame into a `deque` (double-ended queue). This `deque` acts as a thread-safe buffer, decoupling the high-priority audio capture from the potentially variable workload of the STT processing.

3.  **STT Processing (Dedicated Thread):** A separate thread, `process_audio`, runs in a continuous loop.

    - It pulls audio frames from the `deque`.
    - It feeds the raw audio waveform into the `sherpa-onnx` `OnlineRecognizer` stream via the `accept_waveform` method.
    - It continuously calls `recognizer.is_ready` and `recognizer.decode_stream` to process the audio incrementally.
    - The partial or final recognition result is retrieved using `recognizer.get_result`.

4.  **Text Normalization and Consumption (Navigator Thread):**
    - The raw text from the STT engine is immediately normalized using the `text_normalizer` utility. This critical step ensures the transcribed text has the same canonical format (lowercase, numbers as words, no punctuation) as the pre-processed `Chunk` data.
    - The most recent 12 normalized words are maintained in a separate "recent words" `deque`. This sliding window of the speaker's most recent utterance is then passed to the `SimilarityCalculator` for analysis by the navigator thread, completing the pipeline from sound to action.
