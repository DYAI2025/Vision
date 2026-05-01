# Repository-Analyse, Funktionstest, Bug-Liste & Startpunkt-Design (Stand: 2026-05-01)

## 1) Testumfang und Methode

Ich habe alle aktuell implementierten, testbaren Komponenten über ihre jeweiligen pytest-Suites validiert:

- `whatsorga-ingest`
- `hermes-runtime`
- `backlog-core`
- `gbrain-bridge`
- `kanban-sync`
- `cli`

Zusätzlich wurde der systemweite Smoke-Test geprüft, der aktuell in dieser Umgebung wegen fehlender Docker/Compose-Voraussetzungen erwartbar nicht ausführbar ist.

---

## 2) Aktueller Stand je Funktionalität

## A. Plattform-/Architekturstatus

- Das Repo ist **Phase-1 Bootstrap** orientiert: service skeletons, health endpoints, basis deployment scripts, erste CI-Checks.
- Die meisten Fachfunktionen aus Phase 2–7 sind noch **nicht implementiert** (laut `3-code/tasks.md` gezielt `Todo`).

## B. Komponenten-Status

### 1. whatsorga-ingest
- **Vorhanden:** Health-Endpunkt (`/v1/health`), Container-/Testgrundlage.
- **Fehlend:** Channel-Adapter (WhatsApp/Voice/Repo), Normalisierungs-Pipeline, Consent-Boundary-Logik.
- **Bewertung:** Skeleton stabil, Produktfunktionalität noch offen.

### 2. hermes-runtime
- **Vorhanden:** Health-Endpunkt, Ollama-Client-Basis.
- **Fehlend:** Event-Consumer, Confidence-Gate, Routing-/Extraction-/Duplicate-Skills, Model-Router/Remote-Profile, Learning-Loop.
- **Bewertung:** Infrastruktur stabil, Kernagentik noch offen.

### 3. backlog-core
- **Vorhanden:** Health-Endpunkt inkl. Postgres-Check, DB-Pool-Lifecycle.
- **Fehlend:** Event-Schema, Audit-Chain, Consent-Tabellen und Endpunkte, RTBF/Retention/Export u. a.
- **Bewertung:** Solider Core-Skeleton, Domainlogik weitgehend offen.

### 4. gbrain-bridge
- **Vorhanden:** Health-Endpunkt, Vault-Basisfunktionen getestet.
- **Fehlend:** Vollständige Page-CRUD-/Schema-/Link-/Redaction-/Audit-Sweep-Funktionalität.
- **Bewertung:** Skeleton stabil, Produktfeatures ausstehend.

### 5. kanban-sync
- **Vorhanden:** Health-Endpunkt, Kanban-Dateisystem-Basisfunktionen.
- **Fehlend:** Card CRUD, Sync-vs-Edit boundary, Move-Detection, Sync-Trigger, RTBF-Cascade-Endpunkt.
- **Bewertung:** Skeleton stabil; ein kritischer Test-/Runtime-Bug wurde gefunden und behoben (siehe Bugliste).

### 6. cli
- **Vorhanden:** `vision health`, Konfigurationsauflösung, Basis-Aggregation.
- **Fehlend:** Source-/Audit-/RTBF-/Export-/Backup-/Review-/Rotate-Befehle.
- **Bewertung:** Guter operativer Einstieg für Health, aber nicht vollständige Operator-Funktionalität.

---

## 3) Gefundene Bugs

## BUG-001 (kritisch) – Schreibbarkeitsprüfung im `kanban-sync`

- **Ort:** `3-code/kanban-sync/app/kanban.py`
- **Symptom:** Test `test_is_writable_false_for_read_only_directory` scheiterte in Root-ähnlicher Umgebung.
- **Ursache:** `os.access(..., W_OK)` kann für privilegierte Nutzer trotz `0555` unerwartet `True` liefern.
- **Risiko:** Falsche "writable"-Erkennung kann Health-/Readiness-Signale verfälschen, insbesondere in Container-/CI-Kontexten.
- **Fix:** Schreibbarkeitslogik auf Modus-Bit-Prüfung (`stat.S_IWUSR|S_IWGRP|S_IWOTH`) + Read-Access-Prüfung umgestellt.
- **Status:** Behoben und verifiziert (Tests grün).

## Nicht-Bug, aber relevante Einschränkungen

1. **Smoke-Test nicht ausführbar ohne Docker/Compose** in dieser Umgebung.
2. **Viele Funktionen fehlen absichtlich** (Task-Plan Phase 2–7), daher ist der Hauptstatus "nicht implementiert" statt "defekt".

---

## 4) Gesamt-Fixing-Plan (Bug-Sprint)

Da aktuell nur **ein** klarer Bug auf Implementierungsebene aufgefallen ist und dieser bereits behoben wurde, ist ein großer technischer Bug-Sprint im klassischen Sinn noch nicht der Engpass. Der eigentliche Engpass ist die **Feature-Lücke** gegenüber den spezifizierten Anforderungen.

## Sprint-Vorschlag: "Phase-2/3 Stabilitäts- und Funktions-Sprint"

### Sprint-Ziele
1. Von Skeletons zu minimal funktionsfähigem vertikalen Flow.
2. Consent- und Audit-Basis (Phase 2) zuerst.
3. Danach ingest → event → hermes dispatcher Grundkette (Phase 3).

### Sprint-Pakete

#### Paket A — Security/Compliance/Core Foundation (P0/P1)
- Bearer-Auth-Middleware
- Canonical JSON Helper
- Postgres Events + Consent Schema
- Event-Emit Primitive inkl. Hash-Chain Basis

#### Paket B — Core API-Lebensfähigkeit
- Source Register/Update/Revoke/History Endpunkte
- Audit Query + Verify Chain
- CLI Source/Audit Commands

#### Paket C — End-to-End Minimal Flow
- Input-Endpunkt
- Hermes Event Consumer Stub mit Reconnect
- Manual CLI Input Adapter
- Erste proposal pipeline stub

### QA-/Review-Gate pro Paket
- Unit + Integration Tests je Komponente
- Smoke-Subset (lokal/CI)
- Architektur-Review gegen `2-design/*`
- Sicherheitsreview für Auth/Purpose-Limitation

### Kritikalitätsregel
- **Kritische Bugs** (Sicherheits-/Datenintegritätsfehler) sofort hotfix + isoliert.
- **Nicht-kritische Bugs** gesammelt in Sprint-Batches beheben.

---

## 5) Design für klaren Einstiegspunkt in die Application

## Problem
Aktuell fehlt ein "single obvious entrypoint" für neue Operatoren/Entwickler.

## Zielbild: "Golden Path Entry"

### A. Ein einheitlicher Startbefehl
Ein Root-Entrypoint-Skript `scripts/start.sh` (neu) als Standard:

1. prerequisite checks (docker, compose, env)
2. env drift check
3. `docker compose up -d`
4. optional `scripts/ollama-pull.sh` beim ersten Lauf
5. Health-Wait und Abschluss mit klarer URL/CLI-Ausgabe

### B. Ein einheitlicher Statusbefehl
`./scripts/status.sh` (neu):
- Containerstatus
- `vision health`
- kompakte Ampel-Ausgabe (ok/degraded/down)

### C. Ein einheitlicher "erster E2E-Usecase"
`./scripts/first_run_demo.sh` (neu):
- sendet nach Implementierung der Phase-2/3-Endpunkte einen minimalen Demo-Flow
- dokumentiert erwartete Outputs

### D. README "Quickstart in 3 Commands"
Im Root-README ganz oben:
1. `cp .env.example .env`
2. `bash scripts/start.sh`
3. `vision health`

### E. CLI UX-Pfad
`vision` ohne Subcommand sollte künftig Help + "next actions" zeigen:
- "Run `vision health`"
- "Run `vision source register ...`"
- "Run `vision input ...`"

## Akzeptanzkriterien für den Einstiegspunkt
- Neuer Nutzer kann in <10 Minuten vom Clone zu "System healthy".
- Genau ein primärer Startweg in Doku und Runbook.
- Fehlermeldungen geben direkt nächste Aktion (keine Sackgassen).

---

## 6) Nächste konkrete Schritte (priorisiert)

1. Startpunkt-Artefakte umsetzen (`start.sh`, `status.sh`, README-Quickstart).  
2. Phase-2 Paket A (Auth + Schemas + Event-Emit) umsetzen.  
3. Danach Phase-2 Paket B (Source/Audit APIs + CLI).  
4. Danach Phase-3 Minimalflow für echten E2E-Einstieg.  
5. Pro Paket: Tests + Smoke + Review verpflichtend.

