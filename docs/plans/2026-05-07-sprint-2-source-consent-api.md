# Sprint 2 — Source-Consent API und auditierbare Consent-Änderungen

**Datum Sprint-Start:** 2026-05-07  
**Datum Sprint-Abschluss:** 2026-05-07  
**Scrum-Rahmen:** Zweite MVP-Iteration nach Sprint 1. Der Fokus liegt auf einem vertikalen, nutzbaren Operator-Inkrement: Consent nicht nur als Schema speichern, sondern über HTTP anlegen, ändern, widerrufen und auditierbar nachverfolgen.

## Untersuchung des Product Backlogs

Nach Sprint 1 waren im Product Backlog die Phase-2-Fähigkeiten priorisiert: Event-/Audit-Backbone, Source-Registrierung, Consent-Änderung/-Widerruf, History-Abfrage, Audit-Abfragen und CLI-Kommandos. Die für den Nutzer wertvollste nächste vertikale Scheibe ist **nicht** eine weitere reine Datenbank-Grundlage, sondern der erste bedienbare Consent-Management-Pfad in `backlog-core`.

Ausgewählter Sprint-2-Schnitt:

1. `TASK-postgres-events-schema` final reviewen und schließen, weil Source-Änderungen Audit-Events brauchen.
2. `TASK-event-emit-primitive` implementieren, weil jede Source-Änderung ein hash-verkettetes Event erzeugen muss.
3. `TASK-source-registration-endpoint`, `TASK-source-update-endpoint`, `TASK-source-revoke-endpoint` und `TASK-source-history-endpoint` umsetzen, damit Operatoren den Consent-Lebenszyklus funktional nutzen können.
4. CLI- und generische Audit-Abfrage-Endpunkte bewusst nicht in Sprint 2 ziehen, weil sie auf diesem Inkrement aufbauen und den Sprint unnötig überladen hätten.

## Sprintziel

**Operatoren können Eingabequellen über die `backlog-core` HTTP-API registrieren, Consent-Scope oder Retention ändern, Consent widerrufen und die Consent-Historie inklusive Read-as-of-Abfrage einsehen; jede Mutation erzeugt dabei ein hash-verkettetes Audit-Event und eine append-only History-Version.**

## Wertvolles funktionales Inkrement

Das Sprint-2-Inkrement liefert einen ersten durchgängigen Produktnutzen:

- Eine Quelle kann mit explizitem Consent via `POST /v1/sources` angelegt werden.
- Der aktuelle Consent-Zustand ist via `GET /v1/sources/{source_id}` und `GET /v1/sources` lesbar.
- Consent kann enger oder weiter gefasst werden via `PATCH /v1/sources/{source_id}`.
- Consent kann via `POST /v1/sources/{source_id}/revoke` widerrufen werden.
- Die Historie ist via `GET /v1/sources/{source_id}/history` und `?as_of=` auditierbar.
- Jede Änderung läuft über ein Event-Emit-Primitive, das `payload_hash`, `prev_hash` und `hash` erzeugt.

## Sprint Backlog

| Reihenfolge | Product-Backlog-Item | Sprint-Aufgabe | Akzeptanzkriterien | Tests / Prüfung | Status |
|---:|---|---|---|---|---|
| 1 | `TASK-postgres-events-schema` | Bestehende Events-Migration reviewen und abschließen. | Events-Tabelle ist partitioniert, hat dokumentierte Spalten, Constraints, Indizes und initiale Monats-Partitionen. | `pytest`-Schema-Tests bleiben grün; lokale Umgebung überspringt Docker-Postgres-Tests, Non-Postgres-Suite läuft grün. | Done |
| 2 | `TASK-event-emit-primitive` | Hash-verkettetes Event-Emit-Primitive implementieren. | Payload wird canonical-json-gehasht; Event-Hash reagiert auf `prev_hash`; Insert nutzt transaction-scoped advisory lock und gibt persistierte Hash-Metadaten zurück. | `tests/test_events.py` prüft Payload-Hash-Stabilität, Prev-Hash-Sensitivität und Insert-Material; `tests/test_sources.py` prüft die Nutzung des Emit-Primitives aus dem Source-Service. | Done |
| 3 | `TASK-source-registration-endpoint` | `POST /v1/sources` mit erstem History-Eintrag implementieren. | Erfolgreiche Registrierung liefert `201`; Source-State ist `active`; `source.registered` und erste `consent_history`-Zeile entstehen atomar. | Endpoint-Test prüft Auth-Gating, Statuscode, Response und Service-Aufruf; Service-Test prüft Event-Emission, Default-False-Scope und initiale History-Version. | Done |
| 4 | `TASK-source-update-endpoint` | `PATCH /v1/sources/{source_id}` implementieren. | Partial Updates ersetzen Scope und/oder Retention; leere Patches werden abgelehnt; Änderung schreibt Event + History-Version. | Endpoint-Test prüft Validierung und aktualisierte Response; Service-Test prüft Prior-/New-Scope in der History-Version. | Done |
| 5 | `TASK-source-revoke-endpoint` | `POST /v1/sources/{source_id}/revoke` implementieren. | Source wird `revoked`; Event `source.consent_revoked` und History-Version werden angelegt. | Endpoint-Test prüft Revoked-Response und Change-Reason-Weitergabe; Service-Test prüft `revoked`-State und History-Append. | Done |
| 6 | `TASK-source-history-endpoint` | History- und Read-as-of-Endpoint implementieren. | Full History ist abrufbar; `?as_of=` liefert die gültige Version zum Zeitpunkt. | Endpoint-Test prüft ISO-8601-Parsing und History-Response. | Done |
| 7 | Sprint-Transparenz | Product-/Sprint-Backlog aktualisieren, Vollständigkeit prüfen, Review durchführen. | `3-code/tasks.md` spiegelt erledigte Items wider; Tests, Ruff und Mypy laufen; Risiken und Kundennutzen sind dokumentiert. | Abschlussprüfung siehe unten. | Done |

## Definition of Done / Vollständigkeitsprüfung

- [x] Sprintziel als nutzbares, funktionales Inkrement formuliert.
- [x] Sprint Backlog enthält alle Tasks mit Akzeptanzkriterien, Prüfungen und Status.
- [x] Implementierung enthält Tests für Event-Primitive, Source-Service, Source-Endpunkte und Auth-Gating.
- [x] Bestehende Health-, DB- und Migration-Unit-Tests bleiben grün.
- [x] Ruff-Code-Review/Static-Style-Check ist grün.
- [x] Mypy strict ist grün.
- [x] Code Review durchgeführt; dabei gefundene Issues wurden gefixt: UUID-Response-Typen, Ruff-UP017-Zeitstempel, Zeilenlänge, fehlende `canonical_json`-Mypy-Override, Fixture-Typisierung.
- [x] Product Backlog wurde aktualisiert.

## Tests und Code-Review-Ergebnis

Ausgeführt in `3-code/backlog-core`:

- `uv run --frozen pytest -m 'not postgres'` — 34 passed, 28 deselected.
- `uv run --frozen ruff check .` — passed.
- `uv run --frozen mypy .` — passed.
- `uv run --frozen pytest` — 34 passed, 28 skipped. Die `postgres`-markierten Integrationstests wurden in dieser lokalen Umgebung übersprungen; die Non-Postgres-Suite validiert die neue Implementierung ohne Docker-Abhängigkeit.

## Kundennutzen

Der Kunde erhält nach Sprint 2 einen konkreten, bedienbaren Privacy-/Consent-MVP-Baustein: Vor dem späteren Ingest kann der Operator Quellen rechtmäßig registrieren, Consent anpassen oder widerrufen und jederzeit nachvollziehen, welcher Consent-Zustand wann galt. Das reduziert Compliance-Risiko, schafft Auditierbarkeit und ermöglicht im nächsten Sprint, die Ingest-Grenze gegen reale aktuelle Consent-Zustände zu prüfen, statt auf statische oder manuelle Annahmen angewiesen zu sein.

## Offene Follow-ups / bewusst nicht Teil von Sprint 2

- CLI-Kommandos `vision source ...` bauen auf diesen HTTP-Endpunkten auf.
- Generische Audit-Query- und Chain-Verify-Endpunkte nutzen das neue Event-Primitive als Grundlage.
- Cursor-Pagination für größere History-/List-Antworten bleibt im übergreifenden Pagination-Backlog.

**Sprint 2 ist abgeschlossen.**
