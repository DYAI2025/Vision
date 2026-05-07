# Sprint 1 — Consent Foundation und Audit-Backbone Start

**Datum Sprint-Start:** 2026-05-07  
**Scrum-Rahmen:** Erste MVP-Iteration, vertikaler Pfad Richtung manuelle Eingabe → consent-geprüftes Event → Review-/GBrain-Loop.  
**Sprint-Länge:** 1 Woche als technischer Foundations-Sprint.

## Sprintziel

Als erstes nutzbares MVP-Inkrement wird die persistente Consent-Grundlage in `backlog-core` hergestellt: Für jede spätere manuelle oder kanalbasierte Eingabe kann ein Source-Consent als aktueller Zustand und als unveränderliche Historie gespeichert und per Read-as-of-Abfrage nachvollzogen werden.

## Angestrebtes Inkrement

Das Inkrement besteht aus diesen Komponenten:

1. **Planungsartefakt:** Sprintziel, Sprint Backlog, User Stories und Abnahmekriterien sind dokumentiert.
2. **Datenbank-Migration:** `consent_sources` speichert den aktuellen Consent-Zustand pro Quelle.
3. **Datenbank-Migration:** `consent_history` speichert die versionierte, append-only Consent-Historie.
4. **Schema-Gates:** Datenbank-Checks erzwingen `lawful_basis = consent`, gültige Retention-/Statuswerte und explizite boolesche MVP-Consent-Flags.
5. **Read-as-of-Performance:** Ein Index auf `(source_id, changed_at DESC)` unterstützt die spätere Consent-Abfrage zu einem beliebigen Zeitpunkt.
6. **TDD-Testabdeckung:** Integrationstests beschreiben und prüfen Migration, Schemaform, Standardwerte, Constraint-Verhalten, Append-only-Schutz und Read-as-of-Verhalten.
7. **Task-Board-Update:** `TASK-postgres-consent-schema` ist abgeschlossen und beschreibt die technische Lieferleistung.

## Sprint Backlog

| Reihenfolge | User Story | Sprint-Aufgabe | Abnahmekriterien | Status |
|---:|---|---|---|---|
| 1 | **US-register-source-with-consent** — Als Operator möchte ich eine neue Eingabequelle mit explizitem Consent registrieren, damit nachfolgende Eingaben rechtmäßig und nachvollziehbar verarbeitet werden. | `TASK-postgres-consent-schema`: `consent_sources`-Tabelle anlegen. | Quelle hat `source_id`, `actor_id`, `lawful_basis`, `consent_scope`, `retention_policy`, `current_state`, `granted_at`, `granted_by`, `updated_at`; `lawful_basis` akzeptiert nur `consent`; Default-Scope enthält alle MVP-Flags auf `false`. | Done |
| 2 | **US-register-source-with-consent** | `TASK-postgres-consent-schema`: `consent_history`-Tabelle anlegen. | Erstregistrierung kann als Historienzeile ohne Prior-State gespeichert werden; `new_scope`, `new_retention`, `new_state`, `event_id` sind Pflichtfelder. | Done |
| 3 | **US-register-source-with-consent** | Read-as-of-Abfrage vorbereiten. | Index `(source_id, changed_at DESC)` existiert; Query mit `changed_at <= t ORDER BY changed_at DESC LIMIT 1` liefert den letzten gültigen Zustand vor `t`. | Done |
| 4 | **US-revoke-or-update-consent** — Als Operator möchte ich Consent jederzeit ändern oder widerrufen, damit Verarbeitung sofort eingeschränkt oder gestoppt werden kann. | Append-only-Historie absichern. | `UPDATE`/`DELETE` auf `consent_history` werden abgelehnt; Änderungen müssen als neue Version angehängt werden. | Done |
| 5 | **US-revoke-or-update-consent** | Status- und Retention-Checks definieren. | Nur `active`/`revoked` als Source-State und nur `raw_30d`/`derived_keep`/`review_required` als Consent-Retention-Policy werden akzeptiert. | Done |
| 6 | **US-register-source-with-consent** / **US-revoke-or-update-consent** | TDD-Tests schreiben und grün machen. | Tests prüfen Migrationen, Tabellenform, Defaults, `lawful_basis`-Reject, Scope-Flags, Append-only und Read-as-of. | Done |
| 7 | Scrum-Transparenz | Task-Board aktualisieren und Code-Review durchführen. | `3-code/tasks.md` markiert `TASK-postgres-consent-schema` als Done; Review-Notizen dokumentieren Scope, Risiken und nächste Schritte. | Done |

## User Stories und Testkriterien für die Abnahme

### Story 1: Quelle mit Consent registrieren

**Als** Operator  
**möchte ich** eine Eingabequelle mit `source_id`, `actor_id`, `consent_scope`, `retention_policy`, `granted_at` und `granted_by` registrieren,  
**damit** spätere Eingaben nur mit dokumentierter Einwilligung verarbeitet werden.

**Abnahmekriterien:**

- Given eine neue Source, when sie ohne expliziten Scope angelegt wird, then sind alle MVP-Consent-Flags standardmäßig `false`.
- Given eine Source, when `lawful_basis != consent` gespeichert werden soll, then weist die Datenbank den Datensatz ab.
- Given eine Source, when gültige Pflichtfelder gespeichert werden, then kann ihr aktueller Zustand aus `consent_sources` gelesen werden.

### Story 2: Consent-Historie unveränderlich speichern

**Als** Operator  
**möchte ich** jede Registrierung, Änderung und Revocation als neue Historienversion speichern,  
**damit** frühere Consent-Zustände auditierbar bleiben.

**Abnahmekriterien:**

- Given eine erste Consent-Version, when sie als `consent_history` gespeichert wird, then dürfen Prior-Felder `NULL` sein.
- Given eine gespeicherte Historienzeile, when ein Update oder Delete versucht wird, then lehnt die Datenbank die Mutation ab.
- Given mehrere Historienzeilen für eine Source, when der Zustand zu Zeitpunkt `t` abgefragt wird, then wird die letzte Version vor oder genau zu `t` zurückgegeben.

### Story 3: Consent später ändern oder widerrufen können

**Als** Operator  
**möchte ich** Consent enger fassen oder widerrufen können,  
**damit** kommende Ingest-Events sofort gegen den aktuellen Zustand geprüft werden können.

**Abnahmekriterien:**

- Given eine aktive Source, when eine spätere Version mit anderem Scope angehängt wird, then liefert Read-as-of vor der Änderung den alten Scope und nach der Änderung den neuen Scope.
- Given eine Historienversion, when `new_state` gesetzt wird, then akzeptiert die Datenbank nur `active` oder `revoked`.
- Given eine Retention-Policy, when ein unbekannter Wert gesetzt wird, then wird der Datensatz abgelehnt.

## TDD-Ablauf

1. **Rot:** Tests für Consent-Migration, Schemaform, Default-Scope, Constraint-Rejects, Append-only und Read-as-of wurden vor der finalen Migration als gewünschtes Verhalten formuliert.
2. **Grün:** Migration `0002_create-consent-tables.sql` wurde ergänzt, bis die nicht-Docker-Tests liefen und die Docker-gesteuerten Postgres-Tests in einer geeigneten Umgebung ausführbar sind.
3. **Refactor/Review:** Constraint-Namen, Kommentare und die dokumentierte FK-Abweichung zu `events.event_id` wurden verständlich gemacht.

## Code Review

- **Scope-Fit:** Das Inkrement bleibt bewusst klein und liefert nur die Consent-Schema-Grundlage; API-Endpunkte und CLI-Kommandos bleiben eigene Stories im nächsten Sprint.
- **Compliance-Fit:** `lawful_basis = consent` wird am Schema-Gate erzwungen; ältere Consent-Stände sind durch Append-only-Trigger geschützt.
- **Design-Abweichung:** `consent_history.event_id` ist bewusst kein DB-FK auf `events.event_id`, weil die partitionierte `events`-Tabelle einen Composite-PK `(event_id, created_at)` besitzt. Die spätere Source-Endpoint-Story muss diese Referenz vor dem Insert anwendungsseitig validieren.
- **Risiko:** Die Postgres-Integrationstests benötigen Docker/Testcontainers. In dieser lokalen Umgebung ist Docker nicht verfügbar; CI oder VPS muss sie vollständig ausführen.

## Einfachverständlicher 3-Zeiler

1. **Wert für Nutzer:** Das System kann jetzt nachvollziehbar speichern, welche Quelle welche Verarbeitung erlaubt — die Basis für vertrauenswürdige Eingaben.
2. **So kann man testen:** Migrationen anwenden und prüfen, ob ungültige Lawful-Basis/Scope-Werte abgelehnt werden und Read-as-of den richtigen Consent-Stand liefert.
3. **Nächstes Sprintziel:** Eine geschützte Source-API bauen, die `source.registered`, `source.consent_updated` und `source.consent_revoked` Events schreibt und die Consent-Tabellen aktualisiert.
