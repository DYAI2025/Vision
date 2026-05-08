import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { services } from "./appConfig";
import "./styles.css";

type HealthState = "ok" | "degraded" | "down" | "unknown";

type HealthResult = {
  status: HealthState;
  detail: string;
};

interface AuditEvent {
  event_id: string;
  event_type: string;
  actor_id: string;
  created_at: string;
  hash: string;
  payload: Record<string, unknown>;
}

type MemoDraft = {
  summary: string;
  tags: string[];
  suggestedMemo: string;
  confidence: number;
  payload: Record<string, unknown>;
};

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const operatorToken = import.meta.env.VITE_OPERATOR_TOKEN ?? "test-token";

function summarize(text: string, memo: string): MemoDraft {
  const normalized = text.trim().replace(/\s+/g, " ");
  const sentences = normalized.split(/(?<=[.!?])\s+/).filter(Boolean);
  const summary = sentences.slice(0, 2).join(" ").slice(0, 320) || "Noch keine Kommunikation eingegeben.";
  const words = normalized.toLowerCase().match(/[a-zäöüß0-9-]{4,}/g) ?? [];
  const stopWords = new Set(["dass", "eine", "einen", "oder", "aber", "nicht", "noch", "wird", "werden", "haben", "sind", "projekt", "kommunikation"]);
  const counts = new Map<string, number>();
  for (const word of words) {
    if (!stopWords.has(word)) counts.set(word, (counts.get(word) ?? 0) + 1);
  }
  const tags = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([word]) => word);
  const suggestedMemo = memo.trim() || tags[0] || "inbox";
  const confidence = Math.min(0.86, Math.max(0.34, normalized.length / 800 + tags.length / 20));

  return {
    summary,
    tags,
    suggestedMemo,
    confidence,
    payload: {
      source: "frontend-manual",
      kind: "communication.summary_candidate",
      body: normalized,
      semantic_summary: summary,
      evermemos_candidate: suggestedMemo,
      tags,
      confidence,
      review_required: confidence < 0.72,
    },
  };
}

function statusLabel(status: HealthState): string {
  if (status === "ok") return "ok";
  if (status === "degraded") return "degraded";
  if (status === "down") return "down";
  return "unbekannt";
}

function App() {
  const [health, setHealth] = useState<Record<string, HealthResult>>({});
  const [backendError, setBackendError] = useState<string | null>(null);
  const [communication, setCommunication] = useState("Lass uns die neue Projektstruktur in Obsidian abbilden. Vincent: Die Kanbankarten müssen automatisch mit dem Audit-Log verknüpft sein.");
  const [memo, setMemo] = useState("Projekte/Vision/Backlog");
  const [sendState, setSendState] = useState<string>("Bereit zum Speichern.");
  const [auditLog, setAuditLog] = useState<AuditEvent[]>([]);
  const draft = useMemo(() => summarize(communication, memo), [communication, memo]);

  async function refreshHealth() {
    const entries = await Promise.all(
      services.map(async (service) => {
        try {
          const response = await fetch(`${apiBase}${service.healthPath}`, { headers: { Accept: "application/json" } });
          const body = await response.json().catch(() => ({}));
          const status = response.ok ? (body.status ?? "ok") : (body.status ?? "down");
          return [service.id, { status, detail: JSON.stringify(body.checks ?? body) }] as const;
        } catch (error) {
          return [service.id, { status: "unknown", detail: error instanceof Error ? error.message : "nicht erreichbar" }] as const;
        }
      }),
    );
    const healthMap = Object.fromEntries(entries);
    setHealth(healthMap);
    
    // Check if critical Truth Store is down
    if (healthMap["backlog-core"]?.status === "down" || healthMap["backlog-core"]?.status === "unknown") {
      setBackendError("Backend-Verbindung unterbrochen. Bitte 'docker compose up' ausführen.");
    } else {
      setBackendError(null);
    }
  }

  async function loadAudit() {
    try {
      const response = await fetch(`${apiBase}/v1/audit/query?limit=5`, {
        headers: { "Authorization": `Bearer ${operatorToken}`, "Accept": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        setAuditLog(data);
      }
    } catch (e) {}
  }

  async function ensureSourceRegistered() {
    try {
      await fetch(`${apiBase}/v1/sources`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json", 
          "Authorization": `Bearer ${operatorToken}` 
        },
        body: JSON.stringify({
          source_id: "frontend-workbench",
          actor_id: "operator",
          consent_scope: { summarize: true, extract_artifacts: true, learning_signal: true },
          retention_policy: "raw_30d",
          granted_by: "ui"
        }),
      });
    } catch (e) {
      // 409 or network error - either way we proceed
    }
  }

  async function submitIdea() {
    setSendState("Sende Idee an Audit-Log …");
    try {
      await ensureSourceRegistered();

      // 2. Dann Event speichern
      const response = await fetch(`${apiBase}/v1/inputs`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json", 
          "Authorization": `Bearer ${operatorToken}` 
        },
        body: JSON.stringify({
          event_type: "idea.captured",
          payload: draft.payload,
          retention_class: "audit_kept"
        }),
      });

      if (!response.ok) {
        setSendState(`Fehler: HTTP ${response.status}. Logge lokal.`);
      } else {
        setSendState("Idee sicher im Audit-Log festgeschrieben.");
        void loadAudit();
      }
    } catch (error) {
      setSendState("Backend nicht erreichbar. Nutze lokale Vorschau.");
    }
  }

  useEffect(() => {
    void refreshHealth();
    void loadAudit();
  }, []);

  return (
    <main>
      {backendError && (
        <div className="error-banner">
          ⚠️ {backendError}
        </div>
      )}
      <header className="workbench-header">
        <p className="eyebrow">Vision | Idea Workbench</p>
        <h1>Vom Gedanken zur digitalen Wahrheit.</h1>
        <div className="status-summary">
          {services.map(s => (
            <span key={s.id} className={`dot ${health[s.id]?.status ?? 'unknown'}`} title={s.name}></span>
          ))}
          <button className="minimal" onClick={() => void refreshHealth()}>Sync Status</button>
        </div>
      </header>

      <div className="workbench-grid">
        {/* LINKS: INPUT & PROCESSING */}
        <section className="panel workspace">
          <h2>1. Ideenfindung & Erfassung</h2>
          <p className="hint">Beschreibe dein Vorhaben. Hermes analysiert Struktur und Kontext lokal.</p>
          
          <label>
            Gedankengang
            <textarea 
              value={communication} 
              onChange={(e) => setCommunication(e.target.value)} 
              placeholder="Was beschäftigt dich gerade?"
              rows={6} 
            />
          </label>

          <label>
            Ziel-Kontext (Obsidian)
            <input 
              value={memo} 
              onChange={(e) => setMemo(e.target.value)} 
              placeholder="Ordner oder Projektreferenz"
            />
          </label>

          <div className="processing-indicator">
            <span className="pulse"></span>
            Semantische Analyse aktiv (Local Inbound)
          </div>
        </section>

        {/* RECHTS: PREVIEW & DISPOSITION */}
        <section className="panel result-view">
          <h2>2. Semantische Aufbereitung</h2>
          <div className="candidate-card">
            <h3>Zusammenfassung</h3>
            <p>{draft.summary}</p>
            
            <div className="meta-grid">
              <div>
                <small>Matching</small>
                <strong>{draft.suggestedMemo}</strong>
              </div>
              <div>
                <small>Confidence</small>
                <strong>{Math.round(draft.confidence * 100)}%</strong>
              </div>
            </div>

            <div className="tag-list">
              {draft.tags.map(t => <span key={t} className="tag">#{t}</span>)}
            </div>

            <div className="actions-main">
              <button className="primary" onClick={() => void submitIdea()}>Sicher abspeichern</button>
              <button className="secondary">In Obsidian bearbeiten</button>
            </div>
            <p className="status-msg">{sendState}</p>
          </div>
        </section>
      </div>

      {/* UNTEN: AUDIT TRAIL VISUALIZATION */}
      <section className="panel audit-trail">
        <div className="panel-head">
          <h2>3. Digitale Wahrheit (Audit Trail)</h2>
          <button className="minimal" onClick={() => void loadAudit()}>Historie aktualisieren</button>
        </div>
        <div className="audit-list">
          {auditLog.length === 0 ? (
            <p className="empty">Noch keine Events im permanenten Speicher.</p>
          ) : (
            auditLog.map(event => (
              <div key={event.event_id} className="audit-entry">
                <span className="ts">{new Date(event.created_at).toLocaleTimeString()}</span>
                <span className="type">{event.event_type}</span>
                <span className="actor">{event.actor_id}</span>
                <code className="hash">{event.hash.substring(0, 16)}...</code>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="roadmap-compact">
        <h3>System-Integrität</h3>
        <div className="services-mini">
          {services.map(s => (
            <div key={s.id} className="service-item">
              <strong>{s.name}</strong>: {health[s.id]?.status === 'ok' ? 'Funktional' : 'Wartet auf Initialisierung'}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
