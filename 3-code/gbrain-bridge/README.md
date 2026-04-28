# gbrain-bridge

Provides project context lookup from the local vault for hermes-runtime.

## Endpoints

- `GET /v1/health`
- `GET /v1/context/{project_id}?q=...&limit=...`

Context lookup reads markdown files under `${VAULT_PATH}/projects/{project_id}/*.md`, scores lexical matches against `q`, and returns the best snippets.
