export type Service = {
  id: string;
  name: string;
  role: string;
  works: string;
  open: string;
  healthPath: string;
};

export const services: Service[] = [
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

export const roadmap = [
  "MVP-Schnitt vertikal halten: manuelle Kommunikation erfassen → normalisiertes input_event speichern → Hermes erzeugt Summary + Evermemos-Kandidaten → Review → GBrain-Seite schreiben.",
  "Consent und Audit zuerst produktionsfähig machen, weil spätere Semantik ohne nachvollziehbare Berechtigung nicht sicher angewendet werden darf.",
  "Minimalen /v1/inputs-Endpunkt in backlog-core plus operator-token-auth bauen; Frontend sendet zunächst nur manuelle Quellen.",
  "Hermes-Skill für Zusammenfassung und Memo-Fit implementieren: lokal über Ollama, mit Confidence Score und Review-Required bei Unsicherheit.",
  "gbrain-bridge Page CRUD für Markdown-Memos ergänzen; Links und Tags aus Hermes-Vorschlag übernehmen.",
  "Review-Queue als UI-primäre Arbeitsfläche anbinden: annehmen, bearbeiten, verwerfen, anwenden.",
];
