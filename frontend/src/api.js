// import axios from 'axios';

// const API = axios.create({
//   baseURL: 'http://localhost:8000',
//   timeout: 60000,
// });

// // ── Meetings ──────────────────────────────────────────────────────────────────
// export const getMeetings = () => API.get('/meetings/');
// export const getMeeting = (id) => API.get(`/meetings/${id}`);
// export const getMeetingSummary = (id) => API.get(`/meetings/${id}/summary`);
// export const getMeetingActionItems = (id) => API.get(`/meetings/${id}/action-items`);
// export const getMeetingSentiment = (id) => API.get(`/meetings/${id}/sentiment`);
// export const getMeetingTopics = (id, clusters = 3) => API.get(`/meetings/${id}/topics?num_clusters=${clusters}`);
// export const generateFollowUp = (id) => API.post(`/meetings/${id}/follow-up`);

// // ── Ingest ────────────────────────────────────────────────────────────────────
// export const ingestText = (meeting_id, transcript) =>
//   API.post('/ingest/text', { meeting_id, transcript });

// export const ingestAudio = (formData) =>
//   API.post('/ingest/audio', formData, {
//     headers: { 'Content-Type': 'multipart/form-data' },
//   });

// // ── RAG ───────────────────────────────────────────────────────────────────────
// export const askQuestion = (query, top_k = 5) =>
//   API.post('/rag/ask', { query, top_k });

// export const searchChunks = (query, top_k = 5) =>
//   API.post('/rag/search', { query, top_k });

// // ── Analytics ─────────────────────────────────────────────────────────────────
// export const getOverview = () => API.get('/analytics/overview');
// export const getSpeakerAnalytics = (id) => API.get(`/analytics/${id}/speakers`);
// export const getEngagement = (id) => API.get(`/analytics/${id}/engagement`);
// export const getTimeline = (id) => API.get(`/analytics/${id}/timeline`);

// // ── Agent ─────────────────────────────────────────────────────────────────────
// export const runAgent = (id) => API.post(`/agent/${id}/run`);

// export default API;




import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 60000,
});


// ─────────────────────────────────────────────
// 🟢 MEETINGS (NEW + EXISTING)
// ─────────────────────────────────────────────

// Create new meeting (NEW)
export const createMeeting = (title) =>
  API.post("/meetings/create", {
    title,
  });

// Get all meetings
export const getMeetings = () => API.get("/meetings/");

// Get single meeting
export const getMeeting = (id) => API.get(`/meetings/${id}`);


// ─────────────────────────────────────────────
// 🟢 MEETING ANALYTICS
// ─────────────────────────────────────────────

export const getMeetingSummary = (id) =>
  API.get(`/meetings/${id}/summary`);

export const getMeetingActionItems = (id) =>
  API.get(`/meetings/${id}/action-items`);

export const getMeetingSentiment = (id) =>
  API.get(`/meetings/${id}/sentiment`);

export const getMeetingTopics = (id, clusters = 3) =>
  API.get(`/meetings/${id}/topics?num_clusters=${clusters}`);

export const generateFollowUp = (id) =>
  API.post(`/meetings/${id}/follow-up`);


// ─────────────────────────────────────────────
// 🟢 INGEST (manual upload / text)
// ─────────────────────────────────────────────

export const ingestText = (meeting_id, transcript) =>
  API.post("/ingest/text", { meeting_id, transcript });

export const ingestAudio = (formData) =>
  API.post("/ingest/audio", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });


// ─────────────────────────────────────────────
// 🟢 RAG (Q&A SYSTEM)
// ─────────────────────────────────────────────

export const askQuestion = (query, top_k = 5) =>
  API.post("/rag/ask", { query, top_k });

export const searchChunks = (query, top_k = 5) =>
  API.post("/rag/search", { query, top_k });


// ─────────────────────────────────────────────
// 🟢 ANALYTICS
// ─────────────────────────────────────────────

export const getOverview = () =>
  API.get("/analytics/overview");

export const getSpeakerAnalytics = (id) =>
  API.get(`/analytics/${id}/speakers`);

export const getEngagement = (id) =>
  API.get(`/analytics/${id}/engagement`);

export const getTimeline = (id) =>
  API.get(`/analytics/${id}/timeline`);


// ─────────────────────────────────────────────
// 🟢 AGENT
// ─────────────────────────────────────────────

export const runAgent = (id) =>
  API.post(`/agent/${id}/run`);


// ─────────────────────────────────────────────
// 🟢 WEBSOCKET (LIVE AUDIO STREAM)
// ─────────────────────────────────────────────

export const connectLiveTranscription = (meetingId, title = "Live Meeting") => {
  const ws = new WebSocket(
    `ws://127.0.0.1:8000/stream/transcript?meeting_id=${meetingId}&title=${encodeURIComponent(title)}`
  );

  ws.onopen = () => {
    console.log("🟢 WebSocket Connected:", meetingId);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("📝 Transcript:", data);
  };

  ws.onerror = (err) => {
    console.error("🔴 WebSocket Error:", err);
  };

  ws.onclose = () => {
    console.log("🔴 WebSocket Closed");
  };

  return ws;
};


// ─────────────────────────────────────────────
// EXPORT
// ─────────────────────────────────────────────

export default API;