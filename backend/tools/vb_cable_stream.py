"""
Stream meeting audio from VB-Cable into the realtime transcription WebSocket.

Typical Windows setup:
  1. Set your meeting app speaker/output device to "CABLE Input (VB-Audio Virtual Cable)".
  2. Run this client. It records from "CABLE Output" and sends PCM audio to FastAPI.

Usage:
  python -m backend.tools.vb_cable_stream --list-devices
  python -m backend.tools.vb_cable_stream --title "Daily Standup"
  python -m backend.tools.vb_cable_stream --device-index 12 --title "Client Call"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import uuid
from urllib.parse import urlencode

import numpy as np
import pyaudio
import websockets


TARGET_SAMPLE_RATE = 16_000
CHANNELS = 1
FORMAT = pyaudio.paInt16
READ_SECONDS = 0.25
DEFAULT_DEVICE_HINTS = (
    "cable output",
    "vb-audio virtual cable",
    "vb-cable",
)


def list_input_devices() -> None:
    audio = pyaudio.PyAudio()
    try:
        print("\nInput audio devices:\n")
        for index in range(audio.get_device_count()):
            device = audio.get_device_info_by_index(index)
            if int(device.get("maxInputChannels", 0)) <= 0:
                continue

            rate = int(float(device.get("defaultSampleRate", TARGET_SAMPLE_RATE)))
            print(f"  [{index:2d}] {device['name']}  ({rate} Hz)")
    finally:
        audio.terminate()


def find_input_device(audio: pyaudio.PyAudio, name_hint: str | None) -> dict:
    hints = (name_hint.lower(),) if name_hint else DEFAULT_DEVICE_HINTS
    fallback = None

    for index in range(audio.get_device_count()):
        device = audio.get_device_info_by_index(index)
        if int(device.get("maxInputChannels", 0)) <= 0:
            continue

        fallback = fallback or device
        name = str(device.get("name", "")).lower()
        if any(hint in name for hint in hints):
            return device

    if fallback:
        return fallback

    raise RuntimeError("No input audio device found.")


def resample_pcm16(raw: bytes, source_rate: int) -> bytes:
    if source_rate == TARGET_SAMPLE_RATE:
        return raw

    samples = np.frombuffer(raw, dtype=np.int16)
    if samples.size == 0:
        return raw

    duration = samples.size / source_rate
    target_size = max(1, int(math.ceil(duration * TARGET_SAMPLE_RATE)))

    source_x = np.linspace(0, duration, num=samples.size, endpoint=False)
    target_x = np.linspace(0, duration, num=target_size, endpoint=False)
    resampled = np.interp(target_x, source_x, samples).astype(np.int16)

    return resampled.tobytes()


def build_ws_url(base_url: str, meeting_id: str, title: str) -> str:
    query = urlencode({"meeting_id": meeting_id, "title": title})
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


async def receive_transcripts(websocket) -> None:
    async for message in websocket:
        data = json.loads(message)

        if "error" in data:
            print(f"Server error: {data['error']}")
            continue

        if data.get("status") == "done":
            print("Stream finished.")
            return

        transcript = data.get("transcript", "").strip()
        if transcript:
            label = "FINAL" if data.get("is_final") else "LIVE"
            print(f"[{label}] {transcript}")


async def stream_vb_cable(args: argparse.Namespace) -> None:
    audio = pyaudio.PyAudio()
    stream = None

    try:
        if args.device_index is not None:
            device = audio.get_device_info_by_index(args.device_index)
        else:
            device = find_input_device(audio, args.device_name)

        device_index = int(device["index"])
        device_name = device["name"]
        source_rate = int(float(device.get("defaultSampleRate", TARGET_SAMPLE_RATE)))
        frames_per_buffer = max(256, int(source_rate * READ_SECONDS))

        ws_url = build_ws_url(args.ws_url, args.meeting_id, args.title)

        print(f"Using input: [{device_index}] {device_name} ({source_rate} Hz)")
        print(f"Meeting ID: {args.meeting_id}")
        print(f"Connecting: {ws_url}")
        print("Streaming meeting audio. Press Ctrl+C to stop.\n")

        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=source_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=frames_per_buffer,
        )

        async with websockets.connect(ws_url, max_size=None) as websocket:
            receive_task = asyncio.create_task(receive_transcripts(websocket))

            try:
                while True:
                    loop = asyncio.get_running_loop()
                    raw = await loop.run_in_executor(
                        None,
                        lambda: stream.read(
                            frames_per_buffer,
                            exception_on_overflow=False,
                        ),
                    )
                    await websocket.send(resample_pcm16(raw, source_rate))
            except (KeyboardInterrupt, asyncio.CancelledError):
                await websocket.send("END")
                await receive_task

    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        audio.terminate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream VB-Cable audio to the Meeting AI realtime transcript WebSocket."
    )
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--device-index", type=int)
    parser.add_argument("--device-name", help="Input device name hint, e.g. CABLE Output")
    parser.add_argument("--title", default="Live Meeting")
    parser.add_argument("--meeting-id", default=str(uuid.uuid4()))
    parser.add_argument("--ws-url", default="ws://localhost:8000/stream/transcript")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_devices:
        list_input_devices()
        return 0

    try:
        asyncio.run(stream_vb_cable(args))
        return 0
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
