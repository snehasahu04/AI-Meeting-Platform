import React, { useState, useRef, useEffect } from 'react';
import { askQuestion } from '../api';
import { Send, Bot, User } from 'lucide-react';

const EXAMPLE_QUERIES = [
  'What decisions were made about deployment?',
  'What action items were assigned?',
  'Summarise discussions related to Kafka.',
  'What were the main blockers discussed?',
];

export default function RAGChat() {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: "Hi! I'm your meeting intelligence assistant. Ask me anything about your past meetings.",
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(5);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (query) => {
    const q = (query || input).trim();
    if (!q) return;
    setInput('');
    setMessages(m => [...m, { role: 'user', text: q }]);
    setLoading(true);
    try {
      const res = await askQuestion(q, topK);
      setMessages(m => [...m, {
        role: 'ai',
        text: res.data.answer,
        sources: res.data.sources || [],
      }]);
    } catch (err) {
      setMessages(m => [...m, {
        role: 'ai',
        text: `Error: ${err.response?.data?.detail || 'Request failed. Is the backend running?'}`,
        sources: [],
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">💬 RAG Chat</h1>
        <p className="page-subtitle">Ask questions over all your meeting history</p>
      </div>

      {/* Example queries */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
        {EXAMPLE_QUERIES.map(q => (
          <button key={q} className="btn btn-secondary" style={{ fontSize: 12, padding: '6px 12px' }}
            onClick={() => send(q)}>
            {q}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 0, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 260px)' }}>
        {/* Messages */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10,
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                {msg.role === 'ai' && (
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#312e81',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Bot size={14} color="#818cf8" />
                  </div>
                )}
                <div className={`chat-bubble chat-bubble--${msg.role}`}>
                  {msg.text}
                </div>
                {msg.role === 'user' && (
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#1e3a5f',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <User size={14} color="#60a5fa" />
                  </div>
                )}
              </div>
              {/* Sources */}
              {msg.sources?.length > 0 && (
                <details style={{ marginTop: 8, marginLeft: 38 }}>
                  <summary style={{ fontSize: 12, color: '#6b7280', cursor: 'pointer' }}>
                    📚 {msg.sources.length} source chunks
                  </summary>
                  <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {msg.sources.map((s, j) => (
                      <div key={j} style={{ background: '#0a0a14', border: '1px solid #2d2b45',
                        borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                        <div style={{ color: '#6b7280', marginBottom: 4 }}>
                          Meeting: <code>{s.meeting_id?.slice(0, 8)}</code> · Chunk {s.chunk_id}
                        </div>
                        <div style={{ color: '#9ca3af' }}>{s.text?.slice(0, 200)}…</div>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#312e81',
                display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={14} color="#818cf8" />
              </div>
              <div className="chat-bubble chat-bubble--ai">
                <span className="animate-pulse">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-input-row">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginRight: 8 }}>
            <span style={{ fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>Top K:</span>
            <select className="select" style={{ width: 60, padding: '6px 8px' }}
              value={topK} onChange={e => setTopK(Number(e.target.value))}>
              {[3, 5, 8, 10].map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <input
            className="input"
            placeholder="Ask about your meetings…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            disabled={loading}
          />
          <button className="btn btn-primary" onClick={() => send()} disabled={loading || !input.trim()}>
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
