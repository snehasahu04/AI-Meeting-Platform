import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOverview, getMeetings } from '../api';
import { Database, FileText, Layers, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getOverview(), getMeetings()])
      .then(([ov, mt]) => {
        setOverview(ov.data);
        setMeetings(mt.data.slice(0, 5));
      })
      .catch(() => setError('Cannot reach API. Make sure the backend is running on port 8000.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">🧠 Dashboard</h1>
        <p className="page-subtitle">Real-time meeting intelligence overview</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Stats */}
      <div className="stats-grid">
        <StatCard icon={<Database size={22} />} label="Total Meetings"
          value={overview?.total_meetings ?? '—'} color="#818cf8" />
        <StatCard icon={<FileText size={22} />} label="Transcript Chunks"
          value={overview?.total_transcript_chunks ?? '—'} color="#34d399" />
        <StatCard icon={<Layers size={22} />} label="Vectors Indexed"
          value={overview?.total_vectors_indexed ?? '—'} color="#f472b6" />
      </div>

      {/* Recent meetings */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <span className="card-title">Recent Meetings</span>
          <button className="btn btn-secondary" onClick={() => navigate('/meetings')}>
            View All <ArrowRight size={14} />
          </button>
        </div>
        {meetings.length === 0 ? (
          <p style={{ color: '#6b7280', fontSize: 14 }}>No meetings yet. Go to Ingest to add one.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Meeting ID</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {meetings.map(m => (
                  <tr key={m.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{m.id.slice(0, 8)}…</td>
                    <td>{m.title || '—'}</td>
                    <td><StatusBadge status={m.status} /></td>
                    <td style={{ fontSize: 12, color: '#6b7280' }}>
                      {m.created_at ? new Date(m.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td>
                      <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}
                        onClick={() => navigate(`/meetings/${m.id}`)}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="stat-card">
      <div style={{ color }}>{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>{value}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = { done: 'badge-green', processing: 'badge-yellow', error: 'badge-red' };
  return <span className={`badge ${map[status] || 'badge-blue'}`}>{status}</span>;
}

function Loader() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
      <div className="spinner" style={{ width: 36, height: 36 }} />
    </div>
  );
}
