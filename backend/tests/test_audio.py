"""
Audio device enumeration utility.
Run manually to find your microphone device index.

Usage:
    python -m tests.test_audio
"""

import pyaudio


def list_audio_devices():
    p = pyaudio.PyAudio()
    print("\n🎙️  Available audio devices:\n")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        input_ch = dev.get("maxInputChannels", 0)
        marker = "  ← INPUT" if input_ch > 0 else ""
        print(f"  [{i:2d}] {dev['name']}{marker}")
    p.terminate()


if __name__ == "__main__":
    list_audio_devices()
