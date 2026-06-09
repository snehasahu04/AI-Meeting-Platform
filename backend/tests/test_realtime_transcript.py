"""
Quick test client for the real-time transcription WebSocket.

Usage (run from the backend folder):
    python -m tests.test_realtime_transcript

Requirements:
    pip install pyaudio websockets numpy

The script captures audio from your default microphone and streams it to
ws://localhost:8000/stream/transcript, printing transcripts as they arrive.
Press Ctrl+C to stop.
"""

import asyncio
import json
import threading
import pyaudio
import websockets
import numpy as np

WS_URL = "ws://localhost:8000/stream/transcript"

# Audio settings – must match what the server expects
SAMPLE_RATE = 16_000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 4096          # bytes per read (~0.13 s at 16 kHz mono int16)


async def stream_microphone():
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK // 2,   # frames = samples, not bytes
    )

    print("🎙️  Microphone open. Speak now… (Ctrl+C to stop)")

    async with websockets.connect(WS_URL) as ws:

        # Background task: receive and print transcripts
        async def receive_loop():
            async for message in ws:
                data = json.loads(message)
                if "error" in data:
                    print(f"❌ Server error: {data['error']}")
                elif data.get("status") == "done":
                    print("✅ Stream finished.")
                else:
                    tag = "[FINAL]" if data.get("is_final") else "[LIVE] "
                    print(f"📝 {tag} {data['transcript']}")

        recv_task = asyncio.create_task(receive_loop())

        try:
            while True:
                # Read from mic (blocking – run in executor to stay async)
                loop = asyncio.get_event_loop()
                raw = await loop.run_in_executor(
                    None,
                    lambda: stream.read(CHUNK // 2, exception_on_overflow=False)
                )
                await ws.send(raw)

        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n🛑 Stopping…")
            await ws.send("END")
            await recv_task

    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == "__main__":
    asyncio.run(stream_microphone())
