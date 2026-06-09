import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Meetings from './pages/Meetings';
import MeetingDetail from './pages/MeetingDetail';
import Ingest from './pages/Ingest';
import RAGChat from './pages/RAGChat';
import LiveTranscript from './pages/LiveTranscript';
import {
  LayoutDashboard, Mic, Upload, MessageSquare,
  Calendar, Radio, Brain
} from 'lucide-react';
import './App.css';

const navItems = [
  { to: '/',           icon: LayoutDashboard, label: 'Dashboard'   },
  { to: '/meetings',   icon: Calendar,        label: 'Meetings'    },
  { to: '/ingest',     icon: Upload,          label: 'Ingest'      },
  { to: '/live',       icon: Radio,           label: 'Live'        },
  { to: '/chat',       icon: MessageSquare,   label: 'RAG Chat'    },
];

export default function App() {
  return (
    <Router>
      <div className="app-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-brand">
            <Brain size={28} color="#818cf8" />
            <span>Meeting AI</span>
          </div>
          <nav className="sidebar-nav">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'nav-item--active' : ''}`
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="sidebar-footer">
            <div className="status-dot" />
            <span>API Connected</span>
          </div>
        </aside>

        {/* Main content */}
        <main className="main-content">
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/meetings"  element={<Meetings />} />
            <Route path="/meetings/:id" element={<MeetingDetail />} />
            <Route path="/ingest"    element={<Ingest />} />
            <Route path="/live"      element={<LiveTranscript />} />
            <Route path="/chat"      element={<RAGChat />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
