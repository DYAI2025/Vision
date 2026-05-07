import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type HealthState = "ok" | "degraded" | "down" | "unknown";

type Service = {
  id: string;
  name: string;
  role: string;
  works: string;
  open: string;
  healthPath: string;
};

type HealthResult = {
  status: HealthState;
  detail: string;
};

type MemoDraft = {
  summary: string;
  tags: string[];
  suggestedMemo: string;
  confidence: number;
  payload: Record<string, unknown>;
};

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

const services: Service[] = [
  {
    id: "whatsorga-ingest",
    name: "whatsorga-ingest",
    role: "Adapter- und Normalisierungsgrenze für WhatsApp, Voice, Repo-Events und manuelle Eingaben.",
    works: "FastAPI-Skeleton mit /v1/health; Compose-Integration und Service-Token-Umgebung stehen.",
    open: "Echte Adapter, Normalisierung, Consent-Prüfung und POST /v1/inputs fehlen noch.",
    healthPath: "/v1/health/whatsorga-ingest",
  },
  {
    id: "hermes-runtime",
    name: "hermes-runtime",
    role: "Agent Runtime für Routing, Extraktion, Dublettenprüfung, Brain-first Lookup und Learning Loop.",
    works: "FastAPI-Skeleton und Ollama-Client-Grundlage sind vorhanden; lokale Inferenz ist architektonisch vorgesehen.",
    open: "Semantische Skills, Confidence Gate, Vorschlagserzeugung und Prozess-Endpunkte sind offen.",
    healthPath: "/v1/health/hermes-runtime",
  },
  {
    id: "backlog-core",
    name: "backlog-core",
    role: "Event Store, technische Wahrheit, Proposal Pipeline, Audit Log und Rekonstruktion.",
    works: "Postgres-Readiness via /v1/health ist implementiert; Migrations-Grundlage und Event-Schema-Arbeit sind begonnen.",
    open: "Consent-Records, Audit-Hashchain, Input Events, Proposal Lifecycle, RTBF und Export fehlen für das MVP.",
    healthPath: "/v1/health/backlog-core",
  },
  {
    id: "gbrain-bridge",
    name: "gbrain-bridge",
    role: "GBrain/Evermemos Vault Read/Write, Schema-Validierung und bidirektionale Links.",
    works: "Vault-Mount-Readiness ist live über /v1/health prüfbar.",
    open: "Page CRUD, semantisches Einpassen, Link-Generierung, Redaction-Precondition und Obsidian Review-Flow fehlen.",
    healthPath: "/v1/health/gbrain-bridge",
  },
  {
    id: "kanban-sync",
    name: "kanban-sync",
    role: "Synchronisation zwischen Vorschlägen, Obsidian Kanban und Nutzer-Edits.",
    works: "Kanban-Subtree-Writable-Check ist implementiert.",
    open: "Card CRUD, Sync-Boundary und Edit-Attribution sind spätere MVP-plus Schritte.",
    healthPath: "/v1/health/kanban-sync",
  },
];

const roadmap = [
  "MVP-Schnitt vertikal halten: manuelle Kommunikation erfassen → normalisiertes input_event speichern → Hermes erzeugt Summary + Evermemos-Kandidaten → Review → GBrain-Seite schreiben.",
  "Consent und Audit zuerst produktionsfähig machen, weil spätere Semantik ohne nachvollziehbare Berechtigung nicht sicher angewendet werden darf.",
  "Minimalen /v1/inputs-Endpunkt in backlog-core plus operator-token-auth bauen; Frontend sendet zunächst nur manuelle Quellen.",
  "Hermes-Skill für Zusammenfassung und Memo-Fit implementieren: lokal über Ollama, mit Confidence Score und Review-Required bei Unsicherheit.",
  "gbrain-bridge Page CRUD für Markdown-Memos ergänzen; Links und Tags aus Hermes-Vorschlag übernehmen.",
  "Review-Queue als UI-primäre Arbeitsfläche anbinden: annehmen, bearbeiten, verwerfen, anwenden.",
];

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
  const [communication, setCommunication] = useState("Ben: Lass uns die Meeting-Notizen direkt in Evermemos clustern. Vincent: Wichtig ist, dass offene Entscheidungen als Review-Vorschlag sichtbar bleiben.");
  const [memo, setMemo] = useState("Evermemos/Projektgedächtnis/MVP");
  const [sendState, setSendState] = useState<string>("Noch nicht gesendet.");
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
    setHealth(Object.fromEntries(entries));
  }

  async function submitDraft() {
    setSendState("Sende Kandidat an /v1/inputs …");
    try {
      const response = await fetch(`${apiBase}/v1/inputs`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(draft.payload),
      });
      if (!response.ok) {
        setSendState(`Backend noch nicht bereit: HTTP ${response.status}. Payload bleibt lokal kopierbar.`);
        return;
      }
      setSendState("Kandidat wurde vom Backend angenommen.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "unbekannter Fehler";
      setSendState(`Backend nicht erreichbar: ${message}. Payload bleibt lokal kopierbar.`);
    }
  }

  useEffect(() => {
    void refreshHealth();
  }, []);

  return (
    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">Vision MVP Cockpit</p>
          <h1>Semantische Kommunikations-Zusammenfassung mit Evermemos-Fit.</h1>
          <p>
            Dieses Frontend ist bewusst MVP-nah: Es zeigt, welche Architekturteile bereits leben, prüft vorhandene Health-Endpunkte
            und bereitet manuelle Kommunikationsinhalte als semantischen Kandidaten für die spätere Pipeline vor.
          </p>
          <div className="actions">
            <button onClick={() => void refreshHealth()}>Backend-Status aktualisieren</button>
            <a href="#intake">Inhalt vorbereiten</a>
          </div>
        </div>
        <div className="hero-card">
          <span>API Base</span>
          <strong>{apiBase || "same origin"}</strong>
          <small>Für Railway: VITE_API_BASE_URL auf die Caddy/Tailscale-Ingress-URL setzen.</small>
        </div>
      </section>

      <section className="grid">
        {services.map((service) => {
          const state = health[service.id]?.status ?? "unknown";
          return (
            <article className="card" key={service.id}>
              <div className="card-head">
                <h2>{service.name}</h2>
                <span className={`pill ${state}`}>{statusLabel(state)}</span>
              </div>
              <p>{service.role}</p>
              <dl>
                <dt>Funktioniert</dt>
                <dd>{service.works}</dd>
                <dt>Offen</dt>
                <dd>{service.open}</dd>
                <dt>Health</dt>
                <dd>{health[service.id]?.detail ?? "Noch nicht geprüft."}</dd>
              </dl>
            </article>
          );
        })}
      </section>

      <section className="panel" id="intake">
        <div>
          <p className="eyebrow">MVP Intake</p>
          <h2>Kommunikation semantisch vorbereiten</h2>
          <p>
            Bis Hermes und backlog-core die echten Endpunkte liefern, erzeugt die UI lokal eine Vorschau des Payloads. Sobald
            /v1/inputs implementiert ist, kann derselbe Flow direkt angewendet werden.
          </p>
        </div>
        <label>
          Kommunikation
          <textarea value={communication} onChange={(event) => setCommunication(event.target.value)} rows={7} />
        </label>
        <label>
          Evermemos-Ziel oder Kontext
          <input value={memo} onChange={(event) => setMemo(event.target.value)} />
        </label>
        <div className="result">
          <h3>Semantischer Kandidat</h3>
          <p>{draft.summary}</p>
          <p><strong>Einpassen in:</strong> {draft.suggestedMemo}</p>
          <p><strong>Tags:</strong> {draft.tags.length ? draft.tags.join(", ") : "—"}</p>
          <p><strong>Confidence:</strong> {Math.round(draft.confidence * 100)}%</p>
          <pre>{JSON.stringify(draft.payload, null, 2)}</pre>
          <button onClick={() => void submitDraft()}>An Backend anwenden</button>
          <small>{sendState}</small>
        </div>
      </section>

      <section className="panel roadmap">
        <p className="eyebrow">Nächste MVP-Schritte</p>
        <ol>
          {roadmap.map((item) => <li key={item}>{item}</li>)}
        </ol>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
