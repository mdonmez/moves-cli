import sounddevice as sd
import numpy as np
import time
from pathlib import Path
from moves_cli.models import SttModel
from sherpa_onnx import OnlineRecognizer


def test_stt():
    print("Testing STT Model with correct logic")
    print("-" * 30)

    # 1. Load Model
    print(f"\nModel Directory: {SttModel.model_dir}")
    if not SttModel.model_dir.exists():
        print(
            "ERROR: Model directory does not exist! Run 'moves presentation control' once to download models (or rely on model_preparer)."
        )
        return

    try:
        recognizer = OnlineRecognizer.from_transducer(
            tokens=str(SttModel.model_dir / "tokens.txt"),
            encoder=str(SttModel.model_dir / "encoder.int8.onnx"),
            decoder=str(SttModel.model_dir / "decoder.int8.onnx"),
            joiner=str(SttModel.model_dir / "joiner.int8.onnx"),
            num_threads=4,
            decoding_method="greedy_search",
        )
        print("Model loaded successfully.")
    except Exception as e:
        print(f"ERROR loading model: {e}")
        return

    # 2. Setup Stream
    sample_rate = 16000
    stream = recognizer.create_stream()

    # 3. Audio Callback
    def callback(indata, frames, time, status):
        if status:
            print(status)

        # indata is (frames, channels), we need 1D array
        samples = indata[:, 0]
        stream.accept_waveform(sample_rate, samples)

    # 4. Run Recording
    print("\nStarting recording... Speak now! (Press Ctrl+C to stop)")
    try:
        with sd.InputStream(
            channels=1,
            samplerate=sample_rate,
            callback=callback,
            dtype="float32",
            blocksize=1024,
        ):
            while True:
                if recognizer.is_ready(stream):
                    recognizer.decode_stream(stream)

                text = recognizer.get_result(stream)
                if text:
                    print(f"\rTranscribed: {text}", end="", flush=True)

                time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"\nError during recording: {e}")


if __name__ == "__main__":
    test_stt()
