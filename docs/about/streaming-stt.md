# Streaming Speech-to-Text System

## Overview

Real-time responsiveness in `moves` is powered by a low-latency, offline streaming Speech-to-Text (STT) engine implemented within the `PresentationController`. The system continuously transcribes speech with minimal delay, providing the constant text stream necessary for similarity matching and slide navigation.

## Technology Stack

### Core STT Framework

**Library:** `sherpa-onnx`
- High-performance speech recognition toolkit
- ONNX Runtime for efficient cross-platform execution
- Optimized neural network inference
- Entirely offline operation (no network required)

**Key Advantages:**
- **Privacy:** All processing happens locally, no data leaves the machine
- **Latency:** Eliminates network round-trip time
- **Reliability:** No dependency on internet connectivity
- **Performance:** Hardware-accelerated inference via ONNX Runtime

### Acoustic Model

**Model Type:** Pre-trained Nemo Transducer

**Model Location:** `~/.moves/ml_models/nemo-streaming-stt-480ms-int8/`

**Components:**
- `tokens.txt` - Vocabulary and token mappings
- `encoder.int8.onnx` - Audio feature extraction (INT8 quantized)
- `decoder.int8.onnx` - Language model decoder (INT8 quantized)
- `joiner.int8.onnx` - Prediction network (INT8 quantized)

**Transducer Architecture Benefits:**
- **Streaming-Native:** Designed for incremental processing
- **Low Latency:** Emits results without waiting for pauses
- **Accuracy:** Strong performance on continuous speech
- **Efficiency:** INT8 quantization reduces compute requirements

**Model Characteristics:**
- **Context Window:** 480ms audio chunks
- **Quantization:** INT8 (8-bit integers for faster inference)
- **Language:** English (can be extended to other languages)
- **Sample Rate:** 16kHz (standard for speech recognition)

### Decoding Strategy

**Method:** Greedy Search

**How It Works:**
- At each decoding step, select the single most probable token
- No exploration of alternative hypotheses
- Deterministic output for given audio input

**Comparison with Beam Search:**

| Aspect           | Greedy Search          | Beam Search                |
| :--------------- | :--------------------- | :------------------------- |
| Latency          | Minimal (best)         | Higher                     |
| Accuracy         | Good                   | Potentially better         |
| Complexity       | Low (simple)           | High (explores paths)      |
| Memory           | Minimal                | More (tracks hypotheses)   |
| Use Case         | Real-time applications | Offline transcription      |

**Why Greedy for `moves`:**
- Slide navigation requires immediate response
- Latency is paramount concern
- Accuracy is "good enough" for similarity matching
- Phonetic similarity compensates for minor errors
- Simplicity reduces computational overhead

### Recognizer Configuration

```python
recognizer = OnlineRecognizer.from_transducer(
    tokens=str(model_dir / "tokens.txt"),
    encoder=str(model_dir / "encoder.int8.onnx"),
    decoder=str(model_dir / "decoder.int8.onnx"),
    joiner=str(model_dir / "joiner.int8.onnx"),
    num_threads=8,              # Parallel processing threads
    decoding_method="greedy_search"  # Low-latency decoding
)
```

**Thread Configuration:**
- `num_threads=8`: Enables parallel computation
- Balances CPU usage with latency
- Adjustable based on hardware capabilities

## Multi-Threaded Processing Architecture

The system uses four concurrent execution paths to ensure non-blocking, responsive operation:

### Thread 1: Audio Capture (Main Thread)

**Technology:** `sounddevice` library

**Responsibility:** Continuous microphone audio capture

**Configuration:**
- **Sample Rate:** 16,000 Hz (16 kHz)
- **Frame Duration:** 100 milliseconds
- **Channels:** Mono (single channel)
- **Format:** Float32 (floating-point samples)
- **Device:** Default system microphone

**Operation:**
```python
with sd.InputStream(
    samplerate=16000,
    channels=1,
    dtype='float32',
    blocksize=1600,  # 100ms @ 16kHz = 1600 samples
    callback=audio_callback
):
    # Stream runs continuously
```

**Audio Callback:**
- Invoked every 100ms with new audio frame
- Minimal processing: just queue the frame
- Must return quickly to avoid dropped frames
- Thread-safe queue operation

### Thread 2: Asynchronous Audio Buffer

**Data Structure:** `collections.deque` (double-ended queue)

**Purpose:** Decouple audio capture from STT processing

**Configuration:**
```python
audio_queue = deque(maxlen=5)
```

**Characteristics:**
- **Thread-Safe:** Built-in synchronization for concurrent access
- **FIFO Order:** First-in, first-out processing
- **Bounded Size:** `maxlen=5` prevents unbounded memory growth
- **Auto-Eviction:** Oldest frames dropped if queue fills (prevents lag accumulation)

**Buffer Flow:**
1. Audio callback appends new frame: `audio_queue.append(frame)`
2. STT thread pops frame: `audio_queue.popleft()`
3. Empty queue handled gracefully with short wait

**Design Benefits:**
- High-priority capture never blocked by slow processing
- Variable STT workload doesn't affect audio capture
- Bounded memory prevents runaway resource usage
- Simple, reliable producer-consumer pattern

### Thread 3: STT Processing (Dedicated Thread)

**Responsibility:** Convert audio frames to text transcription

**Continuous Processing Loop:**

```python
def process_audio():
    while not shutdown_flag.is_set():
        # 1. Retrieve audio frame
        if audio_queue:
            chunk = audio_queue.popleft()
        else:
            time.sleep(0.001)  # Brief wait if queue empty
            continue
        
        # 2. Feed to recognizer
        stream.accept_waveform(sample_rate=16000, waveform=chunk)
        
        # 3. Process audio incrementally
        while recognizer.is_ready(stream):
            recognizer.decode_stream(stream)
        
        # 4. Retrieve results
        result = recognizer.get_result(stream)
        if result:
            # Process transcription text
            process_result(result)
```

**Processing Steps:**

**1. Waveform Acceptance**
- Feed raw audio to the recognizer stream
- Accumulates audio context for transducer model
- Non-blocking operation

**2. Incremental Decoding**
- `is_ready()`: Checks if sufficient audio for next decoding step
- `decode_stream()`: Advances recognition by one step
- Loop continues until all available audio processed

**3. Result Retrieval**
- `get_result()`: Returns current recognition hypothesis
- May return partial results (word-in-progress)
- Returns final results when word completed

**4. Text Normalization**
```python
normalized_text = text_normalizer.normalize_text(result)
```
- Apply same normalization as chunk preprocessing
- Ensures format compatibility for similarity matching
- Handles numbers, punctuation, unicode, case

### Thread 4: Text Consumption (Navigator Thread)

**Responsibility:** Process transcribed text for slide navigation

**Recent Words Management:**

```python
recent_words = deque(maxlen=window_size)  # window_size = 12
```

**Sliding Window Update:**
1. Normalized text split into words
2. Extract last 12 words: `words[-12:]`
3. Update sliding window: `recent_words.extend(words)`
4. Automatic eviction of oldest words via `maxlen`

**Navigation Loop:**
```python
def navigate_presentation():
    while not shutdown_flag.is_set():
        current_words = list(recent_words)
        
        if len(current_words) >= 12 and current_words != previous_words:
            # Get candidate chunks for current slide
            candidates = get_candidate_chunks(current_section, all_chunks)
            
            # Calculate similarity scores
            input_phrase = ' '.join(current_words)
            results = similarity_calculator.compare(input_phrase, candidates)
            
            # Navigate to best match
            if results:
                best_match = results[0]
                target_section = best_match.chunk.source_sections[-1]
                navigate_to_section(target_section)
                
            previous_words = current_words
        
        time.sleep(0.1)  # 100ms polling interval
```

**Key Features:**
- Only processes when full 12-word window available
- Avoids duplicate processing with `previous_words` check
- Calls `SimilarityCalculator` for matching
- Executes keyboard navigation based on results
- Polls at 100ms intervals for responsiveness

### Thread 5: Keyboard Input Listener (Background Thread)

**Technology:** `pynput.keyboard.Listener`

**Purpose:** Monitor manual keyboard input for user override

**Monitored Keys:**
- **Right Arrow (→):** Manually advance to next slide
- **Left Arrow (←):** Manually return to previous slide  
- **Insert:** Toggle pause/resume automatic navigation
- **Ctrl+C:** Exit presentation control session

**Implementation:**
```python
listener = Listener(on_press=on_key_press)
listener.start()  # Runs in background daemon thread
```

**Key Press Handler:**
```python
def on_key_press(key):
    if key == Key.right:
        navigate_forward()
    elif key == Key.left:
        navigate_backward()
    elif key == Key.insert:
        paused = not paused
    # Ctrl+C handled by Python signal handler
```

**Design Considerations:**
- Daemon thread: Exits automatically when main program exits
- Non-blocking: Doesn't interfere with voice navigation
- Immediate response: Direct keyboard handling without polling
- Override capability: Manual control takes precedence

## Complete Pipeline Flow

**End-to-End Transcription Pipeline:**

```
[Microphone]
    ↓ 100ms audio frames
[Audio Callback] → [Audio Queue (deque)]
    ↓ Pop frame
[STT Thread]
    ↓ accept_waveform()
[Sherpa-ONNX Recognizer]
    ↓ decode_stream()
[Greedy Search Decoder]
    ↓ get_result()
[Raw Transcription Text]
    ↓ text_normalizer.normalize_text()
[Normalized Text]
    ↓ Extract last 12 words
[Recent Words Deque]
    ↓ Join words
[Navigator Thread]
    ↓ compare()
[SimilarityCalculator]
    ↓ Best match
[Target Slide]
    ↓ Keyboard simulation
[Presentation Navigation]
```

## Performance Characteristics

**Latency Breakdown:**

| Stage                  | Typical Latency  | Notes                           |
| :--------------------- | :--------------- | :------------------------------ |
| Audio Capture          | 100ms            | Frame duration                  |
| Queue Transfer         | < 1ms            | Memory operation                |
| STT Decoding           | 50-100ms         | Per frame, model-dependent      |
| Text Normalization     | < 5ms            | CPU-bound, very fast            |
| Similarity Calculation | 50-100ms         | Depends on candidate count      |
| Keyboard Simulation    | < 10ms           | Operating system delay          |
| **Total**              | **200-400ms**    | From speech to slide navigation |

**Throughput:**
- Audio processing: 10 frames/second (real-time)
- Transcription: Continuous stream
- Navigation decisions: As needed (triggered by matches)

**Resource Usage:**
- CPU: 15-30% on modern multi-core processors
- Memory: ~500MB (primarily model weights)
- Threads: 5 concurrent threads
- GPU: Optional (ONNX Runtime can leverage if available)

## Error Handling and Robustness

**Audio Capture Errors:**
- Microphone unavailable: Graceful error message on startup
- Frame drops: Queue serves as buffer
- Device switching: Requires restart

**Recognition Errors:**
- Malformed audio: Skipped silently, next frame processed
- Model loading failure: Error on initialization with clear message
- Decoder stuck: Timeout and reset mechanisms

**Threading Errors:**
- Exception in thread: Logged, thread continues if possible
- Shutdown coordination: `shutdown_flag` ensures clean exit
- Resource cleanup: All threads properly joined on exit
