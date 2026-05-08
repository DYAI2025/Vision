import React, { useState, useEffect } from 'react';
import './App.css';

type Tab = 'ingest' | 'graph' | 'logs';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('ingest');
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="nexus-container">
      {/* LEFT: SLACK */}
      <aside className="slack-sidebar">
        <div className="header-box">
          <span>COMM_FEED</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '9px' }}>SLACK/SECURE</span>
        </div>
        <div className="slack-feed">
          <div className="slack-msg">
            <div className="msg-meta">14:02 • <span className="msg-user">hermes</span></div>
            Backlog sync with GBrain completed successfully.
          </div>
          <div className="slack-msg">
            <div className="msg-meta">13:58 • <span className="msg-user">ben</span></div>
            Nexus UI seems to be the best fit for our modular stack.
          </div>
        </div>
      </aside>

      {/* CENTER: MAIN VIEWPORT */}
      <main className="main-viewport">
        <div className="tabs">
          <div className={`tab ${activeTab === 'ingest' ? 'active' : ''}`} onClick={() => setActiveTab('ingest')}>
            WHATSORGA_INGEST
          </div>
          <div className={`tab ${activeTab === 'graph' ? 'active' : ''}`} onClick={() => setActiveTab('graph')}>
            GBRAIN_GRAPH
          </div>
          <div className={`tab ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}>
            SYSTEM_LOGS
          </div>
        </div>

        <div className="content-area">
          {activeTab === 'ingest' && (
            <>
              <div className="header-box" style={{ background: 'var(--surface)' }}>
                <span>LIVE_INGESTION_STREAM</span>
                <span style={{ color: 'var(--primary)' }}>● LISTENING</span>
              </div>
              <div className="ingest-log">
                <div className="ingest-entry">
                  <span className="ingest-ts">[14:02:11]</span> <span className="ingest-tag">WA</span> ben: "Wir müssen das VPS-Deployment nächste Woche finalisieren."
                </div>
                <div className="ingest-entry">
                  <span className="ingest-ts">[14:02:15]</span> <span style={{ color: 'var(--accent)' }}>[SYSTEM]</span> hermes_detect: Action Item identified.
                </div>
              </div>
            </>
          )}

          {activeTab === 'graph' && (
            <div className="graph-placeholder">
              <svg width="200" height="200" viewBox="0 0 100 100">
                <path d="M50 10 L90 90 L10 90 Z" fill="none" stroke="var(--primary)" strokeWidth="0.5" />
                <circle cx="50" cy="50" r="30" fill="none" stroke="var(--accent)" strokeWidth="0.5" strokeDasharray="2 2" />
                <circle cx="50" cy="10" r="3" fill="var(--primary)" />
                <circle cx="90" cy="90" r="3" fill="var(--primary)" />
                <circle cx="10" cy="90" r="3" fill="var(--primary)" />
                <text x="35" y="55" fill="var(--accent)" fontSize="5">RETRIEVING...</text>
              </svg>
              <a href="#" className="graph-btn">OPEN FULL GBRAIN GRAPH</a>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="ingest-log">
              [INIT] Vision System V1.0 starting...<br />
              [INIT] Loading Hermes Agent... OK<br />
              [INIT] Connecting to EverMemOS (127.0.0.1:8001)... OK<br />
              [INIT] Ingestion Pipeline active.<br />
              [WAIT] Awaiting inputs...
            </div>
          )}
        </div>

        <div className="status-bar">
          <div className="status-item"><div className="status-dot"></div> RADAR_API: ONLINE</div>
          <div className="status-item"><div className="status-dot" style={{ background: 'var(--accent)' }}></div> EVER_MEM: CONNECTED</div>
          <div className="status-item"><div className="status-dot" style={{ background: 'var(--warning)' }}></div> BACKLOG: SYNCING...</div>
          <div style={{ flex: 1, textAlign: 'right' }}>UTC_TIME: <span>{time}</span></div>
        </div>
      </main>

      {/* RIGHT: KANBAN */}
      <aside className="kanban-side">
        <div className="header-box">BACKLOG_BOARD</div>
        <div className="kanban-scroll">
          <div className="col">
            <div className="col-header">01_TODO</div>
            <div className="card">
              Finalize Tailscale private access
              <div className="card-meta"><span>#infra</span> <span>High</span></div>
            </div>
            <div className="card">
              Integrate GBrain MCP tools
              <div className="card-meta"><span>#memory</span> <span>Med</span></div>
            </div>
          </div>
          <div className="col">
            <div className="col-header">02_IN_PROGRESS</div>
            <div className="card">
              Vision Integrative UI Implementation
              <div className="card-meta"><span>#frontend</span> <span style={{ color: 'var(--primary)' }}>ACTIVE</span></div>
            </div>
          </div>
          <div className="col">
            <div className="col-header">03_DONE</div>
            <div className="card" style={{ opacity: 0.5 }}>
              WhatsApp Ingestion Base
              <div className="card-meta"><span>#ingest</span></div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default App;
