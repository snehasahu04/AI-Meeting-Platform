import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ingestText, ingestAudio } from '../api';
import { Upload, FileText, CheckCircle } from 'lucide-react';

export default function Ingest() {
  const [mode, setMode] = useState('text'); // 'text' | 'audio'
  const navigate = useNavigate();

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">📥 Ingest Meeting</h1>
        <p className="page-subtitle">Upload audio or paste a transcript to start processing</p>
      </div>

      <div className="tabs">
        <button className={`tab ${mode === 'text' ? 'tab--active' : ''}`} onClick={() => setMode('text')}>
          <FileText size={14} style={{ marginRight: 6 }} />Paste Transcript
        </button>
        <button className={`tab ${mode === 'audio' ? 'tab--active' : ''}`} onClick={() => setMode('audio')}>
          <Upload size={14} style={{ marginRight: 6 }} />Upload Audio
        </button>
      </div>

      {mode === 'text' ? (
        <TextIngest onSuccess={(id) => navigate(`/meetings/${id}`)} />
      ) : (
        <AudioIngest onSuccess={(id) => navigate(`/meetings/${id}`)} />
      )}
    </div>
  );
}

function TextIngest({ onSuccess }) {
  const [meetingId, setMeetingId] = useState('');
  const [transcript, setTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!transcript.trim()) { setError('Transcript cannot be empty.'); return; }
    setLoading(true); setError('');
    try {
      const res = await ingestText(meetingId || undefined, transcript);
      setResult(res.data);
      onSuccess(res.data.meeting_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Ingestion failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 700 }}>
      {error && <div className="alert alert-error">{error}</div>}
      {result && (
        <div className="alert alert-success">
          <CheckCircle size={16} style={{ marginRight: 8 }} />
          Ingested! Meeting ID: <code>{result.meeting_id}</code> — {result.chunks_indexed} chunks indexed.
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Meeting ID (optional)</label>
          <input className="input" placeholder="Leave blank to auto-generate"
            value={meetingId} onChange={e => setMeetingId(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Transcript *</label>
          <textarea className="textarea" style={{ minHeight: 240 }}
            placeholder="Paste your meeting transcript here…"
            value={transcript} onChange={e => setTranscript(e.target.value)} />
        </div>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Processing…</> : 'Ingest Transcript'}
        </button>
      </form>
    </div>
  );
}

function AudioIngest({ onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) { setError('Please select an audio file.'); return; }
    setLoading(true); setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await ingestAudio(formData);
      setResult(res.data);
      onSuccess(res.data.meeting_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Audio ingestion failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 700 }}>
      {error && <div className="alert alert-error">{error}</div>}
      {result && (
        <div className="alert alert-success">
          <CheckCircle size={16} style={{ marginRight: 8 }} />
          Transcribed! Meeting ID: <code>{result.meeting_id}</code>
          <br />Preview: <em>{result.transcript_preview}</em>
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Audio File (wav, mp3, aac, m4a…)</label>
          <input type="file" accept="audio/*"
            style={{ color: '#d1d5db', fontSize: 14 }}
            onChange={e => setFile(e.target.files[0])} />
        </div>
        {file && (
          <div className="alert alert-info" style={{ marginBottom: 16 }}>
            Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}
        <button className="btn btn-primary" type="submit" disabled={loading || !file}>
          {loading
            ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Transcribing (may take a minute)…</>
            : <><Upload size={15} /> Upload & Transcribe</>}
        </button>
      </form>
    </div>
  );
}
