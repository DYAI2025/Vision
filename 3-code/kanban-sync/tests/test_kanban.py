"""Unit tests for app.kanban: env-driven path config + writability primitive."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from app.kanban import (
    DEFAULT_KANBAN_SUBTREE,
    DEFAULT_VAULT_PATH,
    is_writable,
    kanban_subtree,
    vault_path,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_vault_path_returns_default_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VAULT_PATH", raising=False)
    assert str(vault_path()) == DEFAULT_VAULT_PATH


def test_vault_path_reads_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAULT_PATH", "/custom/vault/location")
    assert str(vault_path()) == "/custom/vault/location"


def test_kanban_subtree_returns_default_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KANBAN_SUBTREE", raising=False)
    assert str(kanban_subtree()) == DEFAULT_KANBAN_SUBTREE


def test_kanban_subtree_reads_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KANBAN_SUBTREE", "/custom/vault/Boards")
    assert str(kanban_subtree()) == "/custom/vault/Boards"


def test_is_writable_true_for_existing_directory(tmp_path: Path) -> None:
    """A real, accessible directory passes the writability check."""
    assert is_writable(tmp_path) is True


def test_is_writable_false_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    assert is_writable(missing) is False


def test_is_writable_false_for_file_not_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "card.md"
    file_path.write_text("not a directory")
    assert is_writable(file_path) is False


def test_is_writable_returns_false_when_access_denied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If effective access is denied, writability folds into False."""
    read_only = tmp_path / "ro-board"
    read_only.mkdir()
    read_only.chmod(0o555)
    original_access = os.access
    expected_mode = os.R_OK | os.W_OK | os.X_OK

    def fake_access(path: Path, mode: int, *args: object, **kwargs: object) -> bool:
        if path == read_only:
            assert mode == expected_mode
            return False
        return original_access(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "access", fake_access)

    try:
        mode = os.R_OK | os.W_OK | os.X_OK
        if os.access in os.supports_effective_ids:
            expected = os.access(read_only, mode, effective_ids=True)
        else:
            expected = os.access(read_only, mode)
        assert is_writable(read_only) is expected
    finally:
        # Restore writable so the tmp_path teardown succeeds.
        read_only.chmod(0o755)


def test_is_writable_uses_effective_permissions_not_mode_bits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Mode bits alone are insufficient when effective UID/GID lacks access.

    This test ensures that `is_writable` delegates to `os.access` with the
    provided path, and that `os.access` is the source of truth even when
    the mode bits would otherwise allow access.
    """
    # Make the mode bits as permissive as possible so the test documents that
    # effective permissions (via os.access) control the result, not the mode.
    tmp_path.chmod(0o777)

    def fake_access(path: Path, mode: int, *args, **kwargs) -> bool:
        # Ensure is_writable calls os.access with the path argument it receives.
        assert path == tmp_path
        # Return False regardless of mode bits to simulate lack of effective access.
        return False

    monkeypatch.setattr(os, "access", fake_access)
    assert is_writable(tmp_path) is False


def test_is_writable_does_not_raise_on_oserror() -> None:
    """A path whose `is_dir()` raises OSError must fold into False, not propagate."""

    class RaisingPath:
        def exists(self) -> bool:
            return True

        def is_dir(self) -> bool:
            raise OSError("simulated fs failure")

    # type: ignore[arg-type] — duck-typed surface is what is_writable actually uses
    assert is_writable(RaisingPath()) is False  # type: ignore[arg-type]


def test_is_writable_handles_non_empty_directory(tmp_path: Path) -> None:
    """Directories with existing kanban-style content still report writable."""
    (tmp_path / "Project A.md").write_text("# Project A")
    (tmp_path / "archives").mkdir()
    assert is_writable(tmp_path) is True


def test_kanban_subtree_default_is_under_default_vault_path() -> None:
    """The Kanban subtree's default path lives inside the default vault path,
    matching the docker-compose.yml mount layout."""
    assert str(kanban_subtree()).startswith(str(vault_path()) + os.sep)
