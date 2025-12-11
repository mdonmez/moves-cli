import sounddevice as sd
import numpy as np
import time


def test_audio():
    print("Testing Audio Input with sounddevice")
    print("-" * 30)

    # 1. List Devices
    print("\nAvailable Devices:")
    print(sd.query_devices())

    default_input = sd.query_devices(kind="input")
    print(f"\nDefault Input Device: {default_input['name']}")

    # 2. Test Recording
    duration = 3  # seconds
    fs = 16000  # Sample rate

    print(f"\nRecording for {duration} seconds... Please speak into your microphone.")

    try:
        recording = sd.rec(
            int(duration * fs), samplerate=fs, channels=1, dtype="float32"
        )

        # Show a simple progress bar
        for i in range(duration):
            print(f"Recording... {i + 1}/{duration}")
            time.sleep(1)

        sd.wait()  # Wait until recording is finished
        print("Recording finished.")

        # 3. Analyze Audio
        max_amplitude = np.max(np.abs(recording))
        print(f"\nMax Amplitude detected: {max_amplitude:.6f}")

        if max_amplitude < 0.001:
            print(
                "WARNING: Very low amplitude detected. Is the microphone muted or volume too low/zero?"
            )
        else:
            print("SUCCESS: Audio signal detected!")

    except Exception as e:
        print(f"\nERROR during recording: {e}")


if __name__ == "__main__":
    test_audio()
