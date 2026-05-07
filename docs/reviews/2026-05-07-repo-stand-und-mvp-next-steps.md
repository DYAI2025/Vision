# Repository-Stand und priorisierte MVP-Next-Steps — 2026-05-07

## 1. Kurzfazit

Das Repository ist aktuell **kein fertiges Ever-MemOS-/WhatsOrga-Produkt**, sondern ein gut strukturierter **Phase-1/Phase-2-Bootstrap**: Architektur, Spezifikation, Deploy-Grundlage, Health-Endpunkte, gemeinsamer Auth-/Canonical-JSON-Unterbau, CLI-Health-Aggregation, ein erster Postgres-Events-Schema-Entwurf und ein Railway-fähiges Frontend-Cockpit sind vorhanden. Der wichtigste fehlende Teil ist der **durchgängige Produktloop**:

> manuelle oder kollaborative Kommunikation → consent-geprüfte Normalisierung → persistiertes Event → Hermes/GBrain-Semantik → Review/Proposal → Obsidian-/Evermemos-Markdown → Lernsignal.

Für den MVP sollte die Arbeit daher **nicht zuerst auf WhatsApp-Automatisierung oder viele Kanäle** verteilt werden. Priorität hat ein schmaler, funktionsfähiger Vertikalschnitt, der zunächst über manuelle Eingabe oder ein eigenes leichtgewichtiges Chat-Frontend läuft und danach sauber um Slack und WhatsApp/WhatsOrga erweitert wird.

## 2. Untersuchungsmethode

Geprüft wurden:

- Repository-Struktur, Branch- und Arbeitsbaumzustand.
- vorhandene Task-Tabelle und Ausführungsplan.
- README, Architektur-, API- und Datenmodell-Dokumente.
- neuere Review-/Planungsdokumente.
- Docker-Compose-Service-Matrix und CI-Konfiguration.
- Backend-/Frontend-Codeoberflächen, insbesondere implementierte Endpunkte und Skeleton-Hinweise.
- lokale Laufzeitumgebung: laufende Container/Compose-Projekte und relevante Prozesse.

Wichtige Einschränkung: In der aktuellen Umgebung ist `docker` nicht installiert. Daher konnten keine real laufenden Compose-Services geprüft werden; die Bewertung von laufenden Projekten basiert auf Repository-Artefakten, Git-Zustand, vorhandenen Prozessen und den deklarierten Compose-/CI-Konfigurationen.

## 3. Aktueller Repository-Status

### 3.1 Gesamtphase

Der Root-README beschreibt das Projekt als **Code-Phase: Phase-1 Bootstrap abgeschlossen, Phase 2 in Arbeit**. Genannt sind sechs ursprüngliche Komponentenskeletons, Install-/Smoke-Skripte und ein Railway-fähiges Frontend-MVP-Cockpit für Service-Health und manuelle semantische Intake-Vorschau.

Die Task-Tabelle enthält aktuell:

| Status | Anzahl | Einordnung |
|---|---:|---|
| Done | 19 | Bootstrap, Service-Skeletons, gemeinsame Helpers, CLI-Health, Install-/Smoke-Skripte, Caddy-Validierung |
| In Progress | 1 | `TASK-postgres-events-schema` |
| Todo | 87 | eigentliche Produktfunktionen ab Consent, Event-Emit, Intake, Proposal, GBrain, Review, Multi-Channel |
| Gesamt | 107 | vollständiger Phasenplan |

### 3.2 Laufende Tasks

Der einzige explizit als **In Progress** markierte Task ist:

- `TASK-postgres-events-schema` — `events`-Tabelle und Indizes gemäß Datenmodell, Priorität P1, abhängig von `TASK-backlog-core-skeleton`.

Diese Markierung passt zum Codezustand: Unter `3-code/backlog-core/migrations/` existiert bereits `0001_create-events-table.sql` mit partitionierter Events-Tabelle, Event-Typ-Checks, Retention-Klassen, Redaction-Konsistenz und Monats-Partitionen von Mai 2026 bis April 2027. Der Task ist aber noch nicht auf `Done` gesetzt; vermutlich fehlen noch vollständige Migration-Integration, Reviews oder Abnahmetests.

### 3.3 Lokal laufende Projekte/Services

In der lokalen Agent-Umgebung wurden keine laufenden Projektservices festgestellt:

- `docker compose config`, `docker ps` und `docker compose ls` konnten nicht ausgeführt werden, weil `docker` fehlt.
- In der Prozessliste liefen keine `uvicorn`, `vite`, `npm`, Projekt-Python-Prozesse, Ollama-, Caddy- oder Compose-Prozesse.
- Sichtbar war nur der MCP-Prozess für PR-Erstellung, also kein Anzeichen eines laufenden Vision-Stacks.

Das bedeutet nicht, dass auf externen VPS-/Railway-Umgebungen nichts läuft; es heißt nur: **in dieser lokalen Arbeitsumgebung läuft kein überprüfbarer Vision-Service**.

## 4. Vorhandene Projekte und Komponenten

### 4.1 Deployment-/Runtime-Projekt

`docker-compose.yml` beschreibt die Ziel-Topologie:

- `postgres` als Event Store.
- `ollama` als lokaler LLM-Runtime-Sidecar.
- `backlog-core` als event-sourced Truth Layer.
- `whatsorga-ingest` für Channel-Adapter und Normalisierung.
- `hermes-runtime` für Agent, lokale Inferenz und Skills.
- `gbrain-bridge` für GBrain-/Obsidian-Vault-Zugriff.
- `kanban-sync` für Obsidian-Kanban-Dateien.
- Ingress über Caddy oder optional Tailscale.
- `cli` als profile-gated Operator-Service.

Die Infrastruktur ist damit gut vorbereitet, aber der Compose-Stack ist in dieser Umgebung nicht live verifizierbar.

### 4.2 `backlog-core`

**Vorhanden:**

- FastAPI-App mit `GET /v1/health`.
- echte Postgres-Pool-/Ping-Prüfung.
- DB-Lifecycle in `app.db`.
- Migration `0001_create-events-table.sql` für die Event-Tabelle.
- Tests für Health, DB-Primitives, Schema und Migrationen.

**Noch offen für MVP:**

- Migration-Runner produktiv einsetzen und `TASK-postgres-events-schema` abschließen.
- Consent-Schema und Source-APIs.
- Event-Emit-Primitive mit Canonical JSON, Payload-Hash und Hash-Chain.
- `POST /v1/inputs`.
- Proposal-Lifecycle, Review-Queue und Dispositionen.
- Audit-Abfragen und Chain-Verifikation.

`backlog-core` ist aktuell der wichtigste Engpass, weil alle nachfolgenden MVP-Funktionen persistierte, auditierbare Events benötigen.

### 4.3 `whatsorga-ingest`

**Vorhanden:**

- FastAPI-Skeleton mit `GET /v1/health`.
- klare Komponentengrenze für Adapter, Normalisierung und Consent-Check.

**Noch offen für MVP:**

- channel-agnostisches `input_event`-Schema.
- manueller Adapter als erster sicherer MVP-Kanal.
- Consent-Snapshot-/Drop-Revoked-Logik.
- spätere WhatsApp-/WhatsOrga-Anbindung ohne Plattform-Bypass.
- optionale Slack-/eigene-Chat-Adapter.

Für MVP sollte `whatsorga-ingest` zunächst **keine echte WhatsApp-Automatisierung** bauen, sondern den manuellen/eigenen Chat-Kanal normieren. WhatsApp/WhatsOrga kann danach an dieselbe Normalisierung angeschlossen werden.

### 4.4 `hermes-runtime`

**Vorhanden:**

- FastAPI-Skeleton mit Health.
- Ollama-Client für lokale Generierung und Embeddings.
- Tests mit MockTransport statt echter Ollama-Abhängigkeit.

**Noch offen für MVP:**

- Events-Consumer oder direkter Summarize-Endpunkt.
- semantische Kommunikationszusammenfassung.
- Vorschlag für Evermemos-/GBrain-Zielseite.
- Extraktion von Entscheidungen, Aufgaben, Kontext und offenen Fragen.
- Confidence Gate.
- Brain-first Lookup gegen GBrain.
- Lernsignale aus Review-Dispositionen.

Für MVP reicht zunächst ein deterministischer, gut getesteter `summary_and_placement_proposal`-Skill, der lokale Ollama-Inferenz kapselt und bei Unsicherheit konsequent Review verlangt.

### 4.5 `gbrain-bridge`

**Vorhanden:**

- FastAPI-Skeleton mit Health.
- Vault-Readiness-Check.
- klare Trennung: GBrain-Bridge darf nicht in den Kanban-Subtree schreiben.

**Noch offen für MVP:**

- Markdown Page CRUD.
- Evermemos-/GBrain-Page-Schema.
- bidirektionale Links.
- Redaction-Precondition vor Persistenz.
- Apply-Endpunkt für approved proposals.
- Obsidian-kompatible Dateinamen, Frontmatter und Linkformat.

Dieser Teil ist für den MVP erfolgskritisch, weil erst hier aus einer semantischen Zusammenfassung ein nutzbarer Evermemos-/Obsidian-Artefakt wird.

### 4.6 `kanban-sync`

**Vorhanden:**

- FastAPI-Skeleton mit Health.
- Schreibbarkeitsprüfung des Kanban-Subtrees.
- Komponentenregel: nur `kanban-sync` schreibt nach `/Kanban`.

**Noch offen für MVP:**

- Card CRUD.
- sync-owned vs. user-owned Frontmatter-Grenze.
- manuelle Spaltenverschiebungen und Attribution.

Für den Evermemos-MVP ist Kanban nützlich, aber nachrangig gegenüber GBrain-Markdown und Review. Es sollte nicht der erste Schreibpfad sein, sofern das Ziel primär semantisches Projektgedächtnis ist.

### 4.7 `cli`

**Vorhanden:**

- Typer-CLI `vision`.
- `vision health` aggregiert Health-Endpunkte der fünf Backendservices.
- Konfigurationslogik für `VISION_BASE_URL` und Operator-Token.

**Noch offen für MVP:**

- `vision source` für Consent-Quellen.
- `vision input` für manuelle Kommunikation.
- `vision review` für CLI-Fallback-Review.
- `vision audit`, `vision rtbf`, `vision export` später.

Der CLI bleibt wichtig als robuste Operator-Fallback-Oberfläche, sollte aber für MVP parallel zum Frontend und nicht als alleinige Nutzeroberfläche gedacht werden.

### 4.8 `frontend`

**Vorhanden:**

- Vite/React-App unter `3-code/frontend`.
- Service-Health-Dashboard gegen Ingress-Health-Routen.
- lokale semantische Preview für Kommunikationsinhalt.
- Payload-Vorschau für zukünftiges `POST /v1/inputs`.
- Railway-Konfiguration.

**Noch offen für MVP:**

- echte Backend-Anbindung an `POST /v1/inputs`.
- Anzeige backend-generierter Proposals.
- Review-Actions: accept, edit, reject, apply.
- Auth-/Token-Handling für Browser-Kontext.
- Anzeige von geschriebenen GBrain-/Evermemos-Seiten.

Das Frontend ist aktuell ein wertvoller **MVP-Vertrag**: Es zeigt, welches Backend als nächstes gebaut werden muss, ohne den Backend-Status zu verschleiern.

## 5. Wichtigste vorhandene Planungs- und Review-Dokumente

- `docs/reviews/2026-05-07-architecture-mvp-frontend-analysis.md` empfiehlt bereits denselben Vertikalschnitt: manuelle Kommunikation → Event-Persistenz → Hermes-Zusammenfassung und Platzierungsvorschlag → Review → GBrain/Evermemos-Markdown.
- `docs/reviews/2026-05-01-repo-analysis-and-bug-sprint-plan.md` ordnet den Stand als Phase-1-Bootstrap ein und schlägt zuerst Consent-/Audit-Foundation, dann Core API, dann Minimal-E2E vor.
- `3-code/tasks.md` ist weiterhin der kanonische Task-Plan, aber für MVP sollte innerhalb des Plans eine stärkere Vertikalschnitt-Priorisierung vorgenommen werden.

## 6. MVP-Zielbild

Der nächste MVP sollte beweisen:

1. Ein Mensch gibt Kommunikationsinhalt ein — zunächst Frontend oder CLI, später Slack/WhatsApp/WhatsOrga.
2. `whatsorga-ingest` normalisiert den Inhalt zu einem einheitlichen `input_event`.
3. `backlog-core` prüft Consent-Kontext und speichert ein auditierbares `input.received` Event.
4. `hermes-runtime` erzeugt eine semantische Zusammenfassung, extrahiert Entscheidungen/Aufgaben/Kontext und schlägt ein Evermemos-/GBrain-Ziel vor.
5. `backlog-core` speichert daraus ein Proposal mit Confidence und Gate-Entscheidung.
6. Ein Mensch reviewed das Proposal im Frontend, per CLI oder perspektivisch in Obsidian.
7. `gbrain-bridge` schreibt nach Freigabe eine Markdown-Seite oder aktualisiert eine vorhandene Evermemos-/GBrain-Seite mit Frontmatter, Links und Audit-Referenz.
8. Die Review-Disposition erzeugt ein Lernsignal, damit Hermes bei ähnlichen Eingaben besser routet.

## 7. Priorisierte Arbeit nach MVP-Wirkung

### P0 — Blocker für jeden Produktloop

1. **`TASK-postgres-events-schema` abschließen.** Ohne stabile Events-Tabelle gibt es keine auditierbare Wahrheit.
2. **Migration-Runner und Event-Emit-Primitive fertigstellen.** Anwendungen dürfen nicht direkt ad hoc SQL schreiben; jedes Domain-Event braucht Canonical JSON, Hash und Chain-Kontext.
3. **Bearer-Auth auf alle nicht-public MVP-Endpunkte anwenden.** Der gemeinsame Auth-Unterbau existiert; die tatsächlichen Mutations- und Read-Endpunkte müssen ihn verwenden.
4. **Consent-Schema und Source-Registration implementieren.** MVP-Kommunikation darf nicht in Semantik laufen, solange Quelle, Zweck und Retention nicht nachvollziehbar sind.

### P1 — Schmaler End-to-End-MVP

5. **`POST /v1/inputs` in `backlog-core`.** Das Frontend zielt bereits darauf; der Endpunkt ist die zentrale Integrationskante.
6. **Minimaler `whatsorga-ingest`-Manual-Adapter.** Erst manuell/eigener Chat, dann Slack/WhatsApp.
7. **Hermes-Summary-and-Placement-Skill.** Ergebnis: Summary, extracted artifacts, suggested Evermemos target, confidence, required_review flag.
8. **Proposal-Endpunkte.** `POST /v1/proposals`, `GET /v1/proposals/:id`, Liste/Queue für Review.
9. **GBrain Markdown CRUD.** Zunächst create/update einer klar definierten Evermemos-Seite mit Frontmatter und Backlink auf Event/Proposal.
10. **Frontend von lokaler Preview auf Backend-Proposals umstellen.** Lokale Preview bleibt als Offline-Fallback, aber die echte Quelle wird backlog-core/Hermes.
11. **Review-Actions im Frontend.** Accept/Edit/Reject/Apply mit auditierter Disposition.

### P1.5 — Kollaborativer Chat nach dem Kernloop

12. **Eigenen minimalen Chat als erster kollaborativer Kanal prüfen.** Vorteil: vollständige Kontrolle über Consent, Identitäten, Exportformat, Thread-IDs und Review-Kontext.
13. **Slack-Adapter als nächster externer Kanal.** Vorteil: stabile APIs und bessere Bot-/Webhook-Modelle als WhatsApp. Slack eignet sich als pragmatische Brücke für kollaborative Architekturtests.
14. **WhatsApp/WhatsOrga erst nach bewiesenem Normalisierungs- und Consent-Pfad.** WhatsApp ist wegen Plattformregeln, Session-/Export-Modell und Datenschutz riskanter. Die Integration sollte sich auf user-consented Exporte oder einen vorhandenen WhatsOrga-konformen Adapter stützen, nicht auf Plattform-Bypass.

### P2 — Obsidian- und Lernloop-Ausbau

15. **Obsidian Review-Queue und Watch-Script.** Sinnvoll, sobald Frontend-/CLI-Review funktioniert.
16. **Brain-first Lookup.** Vor jedem neuen Evermemos-Eintrag sollen relevante GBrain-Seiten zitiert werden, um Dubletten und falsche Cluster zu reduzieren.
17. **Bidirektionale Links und Duplicate Detection.** Macht das Gedächtnis brauchbar und verhindert unkontrolliertes Anwachsen.
18. **Learning Loop.** Review-Korrekturen müssen in Hermes-Kontext und Routingregeln zurückfließen.

### P3 — Operability und Multi-Channel-Härtung

19. **RTBF, Export, Retention Sweep.** Nicht optional für Produktion, aber für einen internen Tech-MVP nach Consent/Audit zunächst nachgelagert, solange Datenmenge und Nutzerkreis kontrolliert sind.
20. **Backup/Restore, Secret Rotation, Reconciliation.** Für VPS-Produktion zwingend, aber nach dem ersten vertikalen Funktionsbeweis.
21. **Performance-Tests und Cross-Provider-Verifikation.** Nach stabilen Endpunkten.

## 8. Empfohlene Sprint-Reihenfolge

### Sprint A — Event- und Consent-Fundament

**Ziel:** backlog-core wird zur echten, auditierbaren Truth-Schicht.

1. `TASK-postgres-events-schema` fertigstellen und auf `Done` setzen.
2. `TASK-postgres-consent-schema`.
3. `TASK-event-emit-primitive`.
4. `TASK-hash-chain-verify`.
5. `TASK-source-registration-endpoint` und `TASK-source-history-endpoint`.
6. minimale CLI- oder HTTP-Tests für Source Registration und Audit Chain.

**Abnahmekriterium:** Eine registrierte Quelle kann ein Event erzeugen; Event ist hashbar, chain-verifizierbar und consent-referenzierbar.

### Sprint B — Manual Intake bis Proposal

**Ziel:** erster Backend-gestützter Kommunikationsfluss.

1. `TASK-idempotency-middleware` für alle Mutationen.
2. `TASK-whatsorga-normalization`.
3. `TASK-whatsorga-manual-cli-adapter` oder direkter Frontend-Manual-Adapter gegen `POST /v1/inputs`.
4. `TASK-whatsorga-consent-check`.
5. `TASK-input-event-endpoint`.
6. Hermes: minimaler Summarize-/Placement-Endpunkt oder Consumer.
7. `TASK-proposal-pipeline-endpoint`.

**Abnahmekriterium:** Ein Kommunikationsabschnitt erzeugt ein `input.received` Event und ein Proposal mit Summary, Zielseite, Confidence und Review-Status.

### Sprint C — Review und Evermemos-Schreibpfad

**Ziel:** aus einem Proposal wird nach Review ein Obsidian-/GBrain-Artefakt.

1. `TASK-proposal-detail-endpoint`.
2. `TASK-review-queue-endpoints`.
3. `TASK-proposal-disposition-endpoint`.
4. `TASK-gbrain-page-schema-validator`.
5. `TASK-gbrain-page-crud`.
6. `TASK-gbrain-bidirectional-links` in Minimalform.
7. Frontend Review-Ansicht und Apply-Button.

**Abnahmekriterium:** Ein Mensch kann ein Proposal akzeptieren/ändern/ablehnen; akzeptierte oder editierte Proposals schreiben eine Markdown-Datei ins Vault und referenzieren Event/Proposal.

### Sprint D — Kollaborationskanal

**Ziel:** mehrere Menschen können in einem Chat-Kontext Daten für Ever MemOS liefern.

1. eigener minimaler Chat-Endpoint oder Slack-Adapter auswählen.
2. Identitätsmodell auf `actor_id`, `source_id`, `thread_id`, `channel_metadata` abbilden.
3. Adapter an bestehendes Normalisierungsschema anschließen.
4. Frontend zeigt Chat-Thread-Kontext und daraus erzeugte Proposals.
5. WhatsOrga-Adapter vorbereiten: Import-/Webhook-Kontrakt, Consent-Mapping, Thread-/Group-Mapping.

**Abnahmekriterium:** Mindestens zwei Akteure liefern in einem gemeinsamen Thread Inhalte; das System erzeugt daraus überprüfbare Evermemos-Vorschläge.

## 9. Empfehlung zur Chat-Architektur

### Beste Reihenfolge

1. **Eigenes Chat-/Manual-Frontend** für den allerersten MVP.
   - schnellste Iteration,
   - kein Plattformrisiko,
   - volle Kontrolle über Consent und Datenmodell,
   - einfacher Anschluss an `POST /v1/inputs`.
2. **Slack** als erster externer kollaborativer Adapter.
   - gute API-/Webhook-Unterstützung,
   - Threads, Nutzer, Channels sauber modellierbar,
   - geeignet für Team-/Projektkommunikation.
3. **WhatsApp/WhatsOrga** danach.
   - hoher Nutzerwert,
   - aber nur, wenn Consent, Retention, Plattformregeln und Adapter-Vertrag sauber sind.

### Minimaler gemeinsamer Chat-Event-Vertrag

Jeder Kanal sollte auf dasselbe interne Format normalisiert werden:

```json
{
  "source_id": "consent-source-id",
  "actor_id": "person-or-system-id",
  "channel": "manual|vision-chat|slack|whatsapp|whatsorga",
  "thread_id": "stable-thread-or-group-id",
  "message_id": "stable-message-id",
  "occurred_at": "2026-05-07T00:00:00Z",
  "body": "message text or transcript",
  "attachments": [],
  "channel_metadata": {},
  "consent_snapshot": {},
  "retention_class": "raw_30d"
}
```

Dieser Vertrag erlaubt, dass Ever MemOS später aus WhatsOrga, Slack oder eigener Chat-UI dieselben Daten erhält, ohne Hermes, GBrain oder Review-Logik neu zu schreiben.

## 10. Hauptrisiken

| Risiko | Auswirkung | Gegenmaßnahme |
|---|---|---|
| Zu frühe WhatsApp-Automatisierung | Plattform-/Datenschutz-/Session-Probleme blockieren MVP | Erst Manual/eigener Chat, dann Slack, dann WhatsOrga/WhatsApp |
| GBrain-Schreibpfad zu spät | System bleibt Demo ohne echtes Gedächtnis | GBrain CRUD in Sprint C vor Kanban priorisieren |
| Consent/Audit umgangen | MVP ist nicht vertrauenswürdig | Source Registration und Event Chain vor Semantik erzwingen |
| Lokale Frontend-Preview bleibt dauerhaft Ersatz | Nutzer glauben, Backend sei fertig | Preview als Fallback behalten, Backend-Proposals als Wahrheit einführen |
| Zu viele Phasen strikt sequenziell | MVP dauert zu lange | Innerhalb des bestehenden Task-Plans einen Vertikalschnitt priorisieren |

## 11. Konkrete nächste Arbeitspakete ab jetzt

1. `TASK-postgres-events-schema` prüfen, Tests ergänzen, abschließen.
2. `TASK-postgres-consent-schema` direkt danach starten.
3. `TASK-event-emit-primitive` inklusive Hash Chain und Idempotenzvorbereitung.
4. `POST /v1/inputs` minimal entwerfen und in API-Design/Frontend-Vertrag abgleichen.
5. `whatsorga-ingest` Normalisierung für `manual` und `vision-chat` definieren.
6. Hermes Minimal-Skill spezifizieren: `communication_summary`, `decision_candidates`, `task_candidates`, `context_notes`, `suggested_gbrain_page`, `confidence`.
7. GBrain Markdown-Schema festlegen: Frontmatter, backlinks, source event IDs, proposal IDs, retention metadata.
8. Frontend-Review-Mock in echte Proposal-API überführen.
9. Slack/WhatsOrga erst als Adapter-Spezifikation dokumentieren, noch nicht bauen.

## 12. Gesamtbewertung

Das Projekt hat eine solide technische Hülle und eine ungewöhnlich gute Dokumentations-/Entscheidungsbasis. Der Weg zum MVP ist nicht mehr primär Architekturarbeit, sondern **Integrationsarbeit entlang eines einzigen Produktloops**. Wenn die nächsten Sprints konsequent auf `input → event → summary/proposal → review → gbrain write` fokussieren, kann aus dem vorhandenen Bootstrap schnell ein nutzbarer Ever-MemOS-Kern entstehen. Erst danach lohnt sich die Breite: Slack, WhatsOrga/WhatsApp, Voice, Repo-Events, Kanban, Retention-Jobs und Operability-Härtung.
