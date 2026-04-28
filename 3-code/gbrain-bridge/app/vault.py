"""Vault filesystem configuration and readiness primitives.

Skeleton-level (TASK-gbrain-bridge-skeleton). Validates that the GBrain vault
mount declared in `docker-compose.yml` is present and readable. Future tasks
layer page CRUD, schema validation, bidirectional links, redaction
preconditions, the Obsidian command-palette watch script, and the weekly
vault audit sweep on top.

Per `3-code/gbrain-bridge/CLAUDE.component.md`: the vault is mounted at
`VAULT_PATH` (defaults to `/vault`); `<VAULT_PATH>/Kanban/` is **owned by
`kanban-sync`**, not this component, and must not be mutated here.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_VAULT_PATH = "/vault"


def vault_path() -> Path:
    """Read VAULT_PATH from env (default: /vault)."""
    raw = os.environ.get("VAULT_PATH") or DEFAULT_VAULT_PATH
    return Path(raw)


def is_readable(path: Path) -> bool:
    """Return True iff `path` exists, is a directory, and we can list it.

    Never raises — health-probe semantics. Permission errors, missing paths,
    and "is a file not a dir" all fold into False.
    """
    try:
        if not path.exists() or not path.is_dir():
            return False
        # Touch the directory to surface OSError (e.g., EACCES) early.
        for _ in path.iterdir():
            break
        return True
    except OSError:
        return False
