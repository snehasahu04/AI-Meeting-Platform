import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMeetings, createMeeting } from '../api';
import { Eye, RefreshCw, Radio } from 'lucide-react';

export default function Meetings() {
  const [meetings, setMeetings] = useState([]);
  const navigate = useNavigate();

  const load = () => {
    getMeetings().then(r => setMeetings(r.data));
  };

  useEffect(() => {
    load();
  }, []);

  // 🔥 CREATE + START LIVE TRANSCRIPTION
  const startLiveMeeting = async () => {
    try {
      const title = prompt("Enter meeting title:");
      if (!title) return;

      const res = await createMeeting(title);
      const meetingId = res.data.meeting_id;

      // redirect to live page
      navigate(`/live?meetingId=${meetingId}&title=${title}`);

    } catch (err) {
      alert("Meeting creation failed");
      console.log(err);
    }
  };

  return (
    <div>

      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h2>📋 Meetings</h2>

        <button className="btn btn-primary" onClick={startLiveMeeting}>
          <Radio size={14} /> Start New Live Meeting
        </button>
      </div>

      <button onClick={load}>
        <RefreshCw size={14} /> Refresh
      </button>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {meetings.map(m => (
            <tr key={m.id}>
              <td>{m.id}</td>
              <td>{m.title}</td>
              <td>
                <button onClick={() =>
                  navigate(`/meetings/${m.id}`)
                }>
                  <Eye size={14} /> View
                </button>
              </td>
            </tr>
          ))}
        </tbody>

      </table>
    </div>
  );
}