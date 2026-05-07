# vision-frontend

Railway-ready MVP cockpit for the Vision stack. The UI intentionally targets the currently working backend surface: health endpoints through the existing ingress, plus a local semantic preview for manual communication intake.

## What it does now

- Shows the current architecture split across `whatsorga-ingest`, `hermes-runtime`, `backlog-core`, `gbrain-bridge`, and `kanban-sync`; this display data is centralized in `src/appConfig.ts`.
- Calls `/v1/health/<service>` for every backend service through the configured ingress.
- Provides a manual intake form that locally prepares a semantic summary candidate, suggested Evermemos placement, tags, confidence, and a future `/v1/inputs` payload.
- Attempts to POST the payload to `/v1/inputs` when clicked; because that endpoint is still an open backend task, failures are reported as an expected MVP gap rather than hidden.

## Railway deployment

Create a Railway service from this repository with the service root set to `3-code/frontend`.

Required/optional variables:

| Variable | Required | Purpose |
|---|---:|---|
| `VITE_API_BASE_URL` | optional | Public Vision ingress URL, for example `https://vision.example.com`. If omitted, the UI calls the same origin. |
| `FRONTEND_ALLOWED_ORIGIN` | set on Caddy stack | Set in the backend `.env` to the Railway domain so browser fetches are allowed through Caddy. |
| `PORT` | Railway-provided | Consumed by `npm run start` via `vite preview --port ${PORT:-4173}`. |

Railway uses `nixpacks.toml` and `railway.json` in this directory:

```bash
npm ci
npm run build
npm run start
```

## Local development

```bash
cd 3-code/frontend
cp .env.example .env
npm ci
npm run dev
```

For a local Compose ingress, set `VITE_API_BASE_URL=http://localhost` in `.env`. For a Railway deployment, also set `FRONTEND_ALLOWED_ORIGIN` in the Compose/Caddy stack to the Railway app origin unless you explicitly opt into `*` for local/evaluation-only testing.
