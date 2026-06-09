import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  getMeeting, getMeetingSummary, getMeetingActionItems,
  getMeetingSentiment, getMeetingTopics, getEngagement,
  getSpeakerAnalytics, generateFollowUp, runAgent
} from '../api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts';

const TABS = ['Summary', 'Action Items', 'Sentiment', 'Topics', 'Speakers', 'Engagement', 'Agent', 'Follow-up'];

export default function MeetingDetail() {
  const { id } = useParams();
  const [meeting, setMeeting] = useState(null);
  const [activeTab, setActiveTab] = useState('Summary');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState({});
  const [error, setError] = useState({});

  useEffect(() => {
    getMeeting(id).then(r => setMeeting(r.data)).catch(() => {});
  }, [id]);

  const fetch = async (tab) => {
    if (data[tab]) return;
    setLoading(l => ({ ...l, [tab]: true }));
    try {
      let res;
      if (tab === 'Summary')      res = await getMeetingSummary(id);
      if (tab === 'Action Items') res = await getMeetingActionItems(id);
      if (tab === 'Sentiment')    res = await getMeetingSentiment(id);
      if (tab === 'Topics')       res = await getMeetingTopics(id, 3);
      if (tab === 'Speakers')     res = await getSpeakerAnalytics(id);
      if (tab === 'Engagement')   res = await getEngagement(id);
      if (tab === 'Agent')        res = await runAgent(id);
      if (tab === 'Follow-up')    res = await generateFollowUp(id);
      setData(d => ({ ...d, [tab]: res.data }));
    } catch (e) {
      setError(er => ({ ...er, [tab]: e.response?.data?.detail || 'Request failed.' }));
    } finally {
      setLoading(l => ({ ...l, [tab]: false }));
    }
  };

  const handleTab = (tab) => {
    setActiveTab(tab);
    fetch(tab);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">🔍 Meeting Detail</h1>
        {meeting && (
          <p className="page-subtitle">
            {meeting.title} &nbsp;·&nbsp;
            <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{id}</span>
          </p>
        )}
      </div>

      <div className="tabs">
        {TABS.map(t => (
          <button key={t} className={`tab ${activeTab === t ? 'tab--active' : ''}`}
            onClick={() => handleTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <TabContent
        tab={activeTab}
        data={data[activeTab]}
        loading={loading[activeTab]}
        error={error[activeTab]}
        onRetry={() => { setData(d => ({ ...d, [activeTab]: null })); fetch(activeTab); }}
      />
    </div>
  );
}

function TabContent({ tab, data, loading, error, onRetry }) {
  if (loading) return <Spinner />;
  if (error) return (
    <div>
      <div className="alert alert-error">{error}</div>
      <button className="btn btn-secondary" onClick={onRetry}>Retry</button>
    </div>
  );
  if (!data) return (
    <div className="alert alert-info">Click the tab to load data.</div>
  );

  if (tab === 'Summary') return <SummaryTab data={data} />;
  if (tab === 'Action Items') return <ActionItemsTab data={data} />;
  if (tab === 'Sentiment') return <SentimentTab data={data} />;
  if (tab === 'Topics') return <TopicsTab data={data} />;
  if (tab === 'Speakers') return <SpeakersTab data={data} />;
  if (tab === 'Engagement') return <EngagementTab data={data} />;
  if (tab === 'Agent') return <AgentTab data={data} />;
  if (tab === 'Follow-up') return <FollowUpTab data={data} />;
  return null;
}

/* ── Tab components ──────────────────────────────────────────────────────── */

function SummaryTab({ data }) {
  return (
    <div className="card">
      <div className="card-title">AI Summary</div>
      <pre style={{ whiteSpace: 'pre-wrap', color: '#d1d5db', fontSize: 14, lineHeight: 1.7 }}>
        {data.summary}
      </pre>
    </div>
  );
}

function ActionItemsTab({ data }) {
  const items = data.action_items || [];
  return (
    <div className="card">
      <div className="card-title">Action Items ({items.length})</div>
      {items.length === 0 ? (
        <p style={{ color: '#6b7280', fontSize: 14 }}>No action items found.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Task</th><th>Owner</th><th>Deadline</th><th>Status</th></tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i}>
                  <td>{item.task}</td>
                  <td>{item.owner}</td>
                  <td>{item.deadline}</td>
                  <td><span className="badge badge-yellow">{item.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SentimentTab({ data }) {
  const trend = (data.aggregate?.trend || []).map((score, i) => ({ chunk: i, score }));
  const agg = data.aggregate || {};
  const labelColor = { positive: '#34d399', neutral: '#fbbf24', negative: '#f87171' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Average Score</div>
          <div className="stat-value">{agg.avg_score?.toFixed(3)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Overall Sentiment</div>
          <div className="stat-value" style={{ color: labelColor[agg.overall_label] || '#818cf8', fontSize: 22 }}>
            {agg.overall_label?.toUpperCase()}
          </div>
        </div>
      </div>
      {trend.length > 0 && (
        <div className="card">
          <div className="card-title">Sentiment Trend</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2b45" />
              <XAxis dataKey="chunk" stroke="#6b7280" tick={{ fontSize: 11 }} label={{ value: 'Chunk', position: 'insideBottom', offset: -2, fill: '#6b7280', fontSize: 11 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} domain={[-1, 1]} />
              <Tooltip contentStyle={{ background: '#13111e', border: '1px solid #2d2b45', borderRadius: 8 }} />
              <Line type="monotone" dataKey="score" stroke="#818cf8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function TopicsTab({ data }) {
  const topTerms = data.top_terms || {};
  const colors = ['#818cf8', '#34d399', '#f472b6', '#fbbf24', '#60a5fa', '#a78bfa'];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {Object.entries(topTerms).map(([clusterId, terms], i) => (
        <div key={clusterId} className="card">
          <div className="card-title" style={{ color: colors[i % colors.length] }}>
            Cluster {clusterId}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {terms.map(term => (
              <span key={term} className="badge badge-purple">{term}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SpeakersTab({ data }) {
  const speakers = data.speakers || [];
  const colors = ['#818cf8', '#34d399', '#f472b6', '#fbbf24', '#60a5fa'];

  if (speakers.length === 0) {
    return (
      <div className="card">
        <p style={{ color: '#6b7280', fontSize: 14 }}>{data.note || 'No speaker data available.'}</p>
        {data.total_words && <p style={{ color: '#9ca3af', marginTop: 8 }}>Total words: {data.total_words}</p>}
      </div>
    );
  }

  const chartData = speakers.map(s => ({ name: s.name, time: s.speaking_time_seconds }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="card">
        <div className="card-title">Speaking Time (seconds)</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d2b45" />
            <XAxis dataKey="name" stroke="#6b7280" tick={{ fontSize: 12 }} />
            <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#13111e', border: '1px solid #2d2b45', borderRadius: 8 }} />
            <Bar dataKey="time" radius={[4, 4, 0, 0]}>
              {chartData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Speaker</th><th>Time (s)</th><th>%</th><th>Words</th><th>Sentiment</th></tr></thead>
          <tbody>
            {speakers.map((s, i) => (
              <tr key={i}>
                <td>{s.name}</td>
                <td>{s.speaking_time_seconds?.toFixed(1)}</td>
                <td>{s.speaking_percentage}%</td>
                <td>{s.word_count}</td>
                <td>{s.sentiment_avg?.toFixed(3) ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EngagementTab({ data }) {
  const score = data.engagement_score ?? 0;
  const color = score >= 70 ? '#34d399' : score >= 40 ? '#fbbf24' : '#f87171';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="stats-grid">
        <div className="stat-card" style={{ alignItems: 'center' }}>
          <div className="stat-label">Engagement Score</div>
          <div className="stat-value" style={{ color, fontSize: 52 }}>{score}</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>out of 100</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Anomalous Chunks</div>
          <div className="stat-value" style={{ color: '#f87171' }}>{data.anomaly_count ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Sentiment</div>
          <div className="stat-value" style={{ fontSize: 24 }}>
            {data.sentiment_summary?.avg_score?.toFixed(3) ?? '—'}
          </div>
        </div>
      </div>
      {data.anomaly_chunk_indices?.length > 0 && (
        <div className="card">
          <div className="card-title">Anomalous Chunk Indices</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {data.anomaly_chunk_indices.map(i => (
              <span key={i} className="badge badge-red">Chunk {i}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AgentTab({ data }) {
  const esc = data.escalation || {};
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="card">
        <div className="card-title">Escalation Decision</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <span className={`badge ${esc.escalate ? 'badge-red' : 'badge-green'}`}>
            {esc.escalate ? '🔴 ESCALATE' : '🟢 NO ESCALATION'}
          </span>
        </div>
        <p style={{ color: '#9ca3af', fontSize: 14 }}>{esc.reason}</p>
      </div>

      {data.unresolved_discussions?.length > 0 && (
        <div className="card">
          <div className="card-title">Unresolved Discussions</div>
          <ul style={{ paddingLeft: 20, color: '#d1d5db', fontSize: 14, lineHeight: 2 }}>
            {data.unresolved_discussions.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
        </div>
      )}

      {data.prioritised_action_items?.length > 0 && (
        <div className="card">
          <div className="card-title">Prioritised Action Items</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Task</th><th>Owner</th><th>Deadline</th></tr></thead>
              <tbody>
                {data.prioritised_action_items.map((item, i) => (
                  <tr key={i}>
                    <td>{item.task}</td>
                    <td>{item.owner}</td>
                    <td>{item.deadline}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.reminder_message && (
        <div className="card">
          <div className="card-title">Reminder Message</div>
          <p style={{ color: '#d1d5db', fontSize: 14, lineHeight: 1.7 }}>{data.reminder_message}</p>
        </div>
      )}
    </div>
  );
}

function FollowUpTab({ data }) {
  return (
    <div className="card">
      <div className="card-title">Follow-up Email</div>
      <pre style={{ whiteSpace: 'pre-wrap', color: '#d1d5db', fontSize: 14, lineHeight: 1.7 }}>
        {data.follow_up_email}
      </pre>
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
      <div className="spinner" style={{ width: 32, height: 32 }} />
    </div>
  );
}
