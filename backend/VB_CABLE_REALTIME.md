# Realtime Meeting Transcription With VB-Cable

Use this when you want Zoom, Google Meet, Teams, or any browser meeting audio to stream into the project and generate live transcripts.

## 1. Install VB-Cable

Install VB-Cable from:

https://vb-audio.com/Cable/

After install, Windows should show:

- Playback device: `CABLE Input (VB-Audio Virtual Cable)`
- Recording device: `CABLE Output (VB-Audio Virtual Cable)`

## 2. Route meeting audio into VB-Cable

In your meeting app audio settings:

- Speaker/output: `CABLE Input (VB-Audio Virtual Cable)`
- Microphone/input: your normal microphone

This sends the meeting sound into the virtual cable. The project records from `CABLE Output`.

## 3. Start the backend

From the project root:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Make sure `backend/.env` has:

```bash
GROQ_API_KEY=your_key_here
```

## 4. Find the VB-Cable device

From the project root:

```bash
python -m backend.tools.vb_cable_stream --list-devices
```

Look for `CABLE Output`.

## 5. Start live transcription

Auto-detect `CABLE Output`:

```bash
python -m backend.tools.vb_cable_stream --title "Client Meeting"
```

Or use a specific device index:

```bash
python -m backend.tools.vb_cable_stream --device-index 12 --title "Client Meeting"
```

The console will print `[LIVE]` transcript chunks. The backend also saves transcript chunks to the meeting database.

## Troubleshooting

- If the wrong device is selected, run `--list-devices` and pass `--device-index`.
- If there is no transcript, check that the meeting app speaker is set to `CABLE Input`.
- If you cannot hear the meeting, enable Windows "Listen to this device" for `CABLE Output`, or use Voicemeeter to monitor the audio.
- If Groq errors appear, verify `GROQ_API_KEY` and internet access.
