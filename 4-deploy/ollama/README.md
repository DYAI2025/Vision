# Ollama

Ollama is the local model runtime per [`CON-local-first-inference`](../../1-spec/constraints/CON-local-first-inference.md). The default deployment makes **0 remote inference calls** — `hermes-runtime` reaches Ollama via service-name DNS on the internal Docker network.

## Bootstrap behavior

- Service `ollama` defined in [`../../docker-compose.yml`](../../docker-compose.yml).
- Image: `ollama/ollama:latest`. Internal-only; no host port mapping.
- Models persist in the `ollama-models` named volume (`project-agent-system_ollama-models` in `docker volume ls`).
- Healthcheck: `ollama list` every 30 s.
- **Models are NOT auto-pulled.** Ollama starts with an empty model registry. The operator pulls the configured model **once** after `docker compose up` — see "Operator quick-access" below.

## Model selection

`OLLAMA_MODEL` in `.env` controls which Gemma-family model is pulled and which model `hermes-runtime` calls. Default: `gemma3:4b`.

| Model | On-disk | RAM (loaded) | Notes |
|---|---|---|---|
| `gemma3:1b` | ~0.8 GB | ~2 GB | Lightest; minimum hardware |
| `gemma3:4b` *(default)* | ~3.3 GB | ~5 GB | Balanced for the 8 GB reference VPS |
| `gemma3:12b` | ~8.1 GB | ~12 GB | Requires upgraded hardware |
| `gemma2:2b` | ~1.6 GB | ~3 GB | Older gen; lighter footprint |
| `gemma2:9b` | ~5.5 GB | ~8 GB | Older gen; tight on 8 GB VPS |

To override: set `OLLAMA_MODEL` in `.env` **before** running `scripts/ollama-pull.sh`. Changing the model after pull simply pulls the new one alongside; storage grows. Remove unused models with `./scripts/ollama.sh rm <model>`.

## Operator quick-access

After `docker compose up`, pull the configured model **once**:

```bash
./scripts/ollama-pull.sh
```

This invokes `docker compose exec ollama ollama pull "$OLLAMA_MODEL"`. Idempotent: re-running pulls only updated layers.

Other Ollama commands inside the container, via the generic helper:

```bash
./scripts/ollama.sh list                    # list pulled models
./scripts/ollama.sh ps                      # currently loaded models
./scripts/ollama.sh run gemma3:4b "hello"   # one-shot generation
./scripts/ollama.sh pull gemma3:1b          # pull a specific model
./scripts/ollama.sh rm gemma2:2b            # remove an unused model
```

Both helpers require Docker + `docker compose` and the `ollama` service running.

## Disk usage

Plan for 5–15 GB depending on which models are pulled. The `ollama-models` named volume is **not** part of standard backups (`TASK-backup-script`, Phase 7) — model artifacts are public and re-pullable from Ollama's registry, so excluding them from backups keeps backup size small.

## Remote inference (opt-in)

`CON-local-first-inference` allows opt-in remote inference via named profiles, audited per [`REQ-SEC-remote-inference-audit`](../../1-spec/requirements/REQ-SEC-remote-inference-audit.md). The remote-profile configuration mechanism (`hermes-runtime`'s model-router middleware) lands with `TASK-model-router` (Phase 5) and `TASK-remote-inference-profile` (Phase 7) — out of scope for bootstrap.
