import React, { useEffect, useRef, useState } from 'react';
import { MonitorSpeaker, Mic, MicOff, Radio, Trash2 } from 'lucide-react';

const WS_URL = 'ws://127.0.0.1:8000/stream/transcript';
const SAMPLE_RATE = 16000;
const CHUNK_SIZE = 4096;

export default function LiveTranscript() {
  const [status, setStatus] = useState('idle');
  const [sourceLabel, setSourceLabel] = useState('');
  const [lines, setLines] = useState([]);
  const [error, setError] = useState('');
  const [fullTranscript, setFullTranscript] = useState('');

  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const processorRef = useRef(null);
  const streamRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  useEffect(() => {
    return () => stopRecording();
  }, []);

  const createAudioStream = async (mode) => {
    if (mode === 'meeting') {
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: {
          channelCount: 1,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      if (displayStream.getAudioTracks().length === 0) {
        displayStream.getTracks().forEach((track) => track.stop());
        throw new Error(
          'No meeting audio was shared. Select a browser tab/window and enable Share audio.'
        );
      }

      displayStream.getVideoTracks().forEach((track) => {
        track.onended = () => stopRecording();
      });

      return displayStream;
    }

    return navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: SAMPLE_RATE,
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      },
    });
  };

  const startRecording = async (mode = 'microphone') => {
    setError('');
    setStatus('connecting');
    setSourceLabel(mode === 'meeting' ? 'Meeting audio' : 'Microphone');

    try {
      const meetingId = crypto.randomUUID();
      const title = mode === 'meeting' ? 'Connected Meeting' : 'Live Meeting';
      const ws = new WebSocket(
        `${WS_URL}?meeting_id=${meetingId}&title=${encodeURIComponent(title)}`
      );

      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = async () => {
        try {
          const mediaStream = await createAudioStream(mode);
          streamRef.current = mediaStream;

          const audioCtx = new window.AudioContext({
            sampleRate: SAMPLE_RATE,
          });
          audioCtxRef.current = audioCtx;

          const source = audioCtx.createMediaStreamSource(mediaStream);
          const processor = audioCtx.createScriptProcessor(CHUNK_SIZE, 1, 1);
          processorRef.current = processor;

          processor.onaudioprocess = (event) => {
            if (ws.readyState !== WebSocket.OPEN) return;

            const inputData = event.inputBuffer.getChannelData(0);
            const int16Data = new Int16Array(inputData.length);

            for (let i = 0; i < inputData.length; i += 1) {
              const sample = Math.max(-1, Math.min(1, inputData[i]));
              int16Data[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
            }

            ws.send(int16Data.buffer);
          };

          source.connect(processor);
          processor.connect(audioCtx.destination);
          setStatus('recording');
        } catch (captureError) {
          setError(captureError.message);
          stopRecording();
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            setError(data.error);
            return;
          }

          if (data.transcript) {
            setLines((prev) => [
              ...prev,
              {
                text: data.transcript,
                isFinal: data.is_final,
              },
            ]);
            setFullTranscript((prev) => `${prev} ${data.transcript}`);
          }

          if (data.status === 'done') {
            setStatus('stopped');
          }
        } catch (parseError) {
          console.error(parseError);
        }
      };

      ws.onerror = () => {
        setError('WebSocket error. Make sure backend is running on port 8000.');
        setStatus('idle');
      };

      ws.onclose = () => {
        setStatus((current) => (current === 'recording' ? 'stopped' : current));
      };
    } catch (err) {
      setError(err.message);
      setStatus('idle');
    }
  };

  const stopRecording = () => {
    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      processorRef.current?.disconnect();
      audioCtxRef.current?.close();

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('END');
      }

      streamRef.current = null;
      processorRef.current = null;
      audioCtxRef.current = null;
      setStatus('stopped');
    } catch (err) {
      console.error(err);
    }
  };

  const clearTranscript = () => {
    setLines([]);
    setFullTranscript('');
    setSourceLabel('');
    setStatus('idle');
    setError('');
  };

  const isActive = status === 'connecting' || status === 'recording';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Live Transcription</h1>
        <p className="page-subtitle">
          Connect microphone or meeting audio and generate transcripts in real time.
        </p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 24,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        {!isActive ? (
          <>
            <button
              className="btn btn-primary"
              onClick={() => startRecording('meeting')}
            >
              <MonitorSpeaker size={16} /> Connect Meeting Audio
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => startRecording('microphone')}
            >
              <Mic size={16} /> Use Microphone
            </button>
          </>
        ) : (
          <button className="btn btn-danger" onClick={stopRecording}>
            <MicOff size={16} /> Stop Transcription
          </button>
        )}

        <button
          className="btn btn-secondary"
          onClick={clearTranscript}
          disabled={lines.length === 0}
        >
          <Trash2 size={15} /> Clear
        </button>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginLeft: 8,
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background:
                status === 'recording'
                  ? '#22c55e'
                  : status === 'connecting'
                    ? '#fbbf24'
                    : '#6b7280',
              animation: status === 'recording' ? 'pulse 1.5s infinite' : 'none',
            }}
          />

          <span
            style={{
              fontSize: 13,
              color: '#9ca3af',
              textTransform: 'capitalize',
            }}
          >
            {status === 'recording'
              ? `Recording ${sourceLabel}`
              : status === 'connecting'
                ? 'Connecting...'
                : status}
          </span>
        </div>
      </div>

      {status === 'idle' && lines.length === 0 && (
        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          For Google Meet in Chrome, click Connect Meeting Audio, choose the meeting
          tab, and enable Share tab audio. For Zoom/Teams desktop apps, route audio
          through VB-Cable and choose Use Microphone with CABLE Output selected.
        </div>
      )}

      <div className="card" style={{ marginBottom: 20 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <span className="card-title">
            <Radio size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Live Transcript
          </span>

          <span style={{ fontSize: 12, color: '#6b7280' }}>
            {lines.length} segments
          </span>
        </div>

        <div className="transcript-box">
          {lines.length === 0 ? (
            <span style={{ color: '#4b5563' }}>Transcript will appear here...</span>
          ) : (
            lines.map((line, index) => (
              <div
                key={`${line.text}-${index}`}
                className={`transcript-line ${
                  line.isFinal ? 'transcript-line--final' : ''
                }`}
              >
                <span style={{ color: '#4b5563', marginRight: 8 }}>
                  [{index + 1}]
                </span>
                {line.text}
                {line.isFinal && (
                  <span style={{ color: '#34d399', marginLeft: 8, fontSize: 11 }}>
                    saved
                  </span>
                )}
              </div>
            ))
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {fullTranscript && (
        <div className="card">
          <div className="card-title">Full Transcript</div>
          <p
            style={{
              color: '#d1d5db',
              fontSize: 14,
              lineHeight: 1.8,
            }}
          >
            {fullTranscript.trim()}
          </p>
        </div>
      )}
    </div>
  );
}
