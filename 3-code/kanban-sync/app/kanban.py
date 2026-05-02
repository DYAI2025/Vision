"""Kanban-subtree filesystem configuration and readiness primitives.

Skeleton-level (TASK-kanban-sync-skeleton). Per
`3-code/kanban-sync/CLAUDE.component.md` § Interfaces:

- The vault is mounted at `VAULT_PATH` (default `/vault`); reads under the
  vault root are read-only (for project-page link resolution from cards).
- The Kanban subtree is at `KANBAN_SUBTREE` (default `/vault/Kanban`);
  this component has exclusive write authority here. `gbrain-bridge` and
  every other component must NOT mutate this subtree.

Future tasks layer card CRUD, sync-vs-edit boundary detection, manual
column-move attribution, and the periodic sync trigger on top of these
primitives.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_VAULT_PATH = "/vault"
DEFAULT_KANBAN_SUBTREE = "/vault/Kanban"


def vault_path() -> Path:
    """Read VAULT_PATH from env (default: /vault). Read-only access scope."""
    raw = os.environ.get("VAULT_PATH") or DEFAULT_VAULT_PATH
    return Path(raw)


def kanban_subtree() -> Path:
    """Read KANBAN_SUBTREE from env (default: /vault/Kanban). Read/write scope."""
    raw = os.environ.get("KANBAN_SUBTREE") or DEFAULT_KANBAN_SUBTREE
    return Path(raw)


def is_writable(path: Path) -> bool:
    """Return True iff `path` exists, is a directory, and passes write checks.

    Writability here is intentionally strict: the directory must have at least
    one write mode bit set *and* `os.access(path, os.R_OK | os.W_OK | os.X_OK)`
    must report effective read/write/execute access for the current process.

    Never raises — health-probe semantics. Permission errors, missing paths,
    and "is a file not a dir" all fold into False.
    """
    try:
        if not path.exists() or not path.is_dir():
            return False
        mode = os.R_OK | os.W_OK | os.X_OK
        if getattr(os, "supports_effective_ids", None) and os.access in os.supports_effective_ids:
            try:
                return os.access(path, mode, effective_ids=True)
            except NotImplementedError:
                pass
        return os.access(path, mode)
    except OSError:
        return False
