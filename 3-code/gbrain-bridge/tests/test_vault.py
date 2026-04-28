"""Unit tests for app.vault: env-driven path config + readiness primitive."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.vault import DEFAULT_VAULT_PATH, is_readable, vault_path

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_vault_path_returns_default_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VAULT_PATH", raising=False)
    assert str(vault_path()) == DEFAULT_VAULT_PATH


def test_vault_path_reads_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VAULT_PATH", "/custom/vault/location")
    assert str(vault_path()) == "/custom/vault/location"


def test_is_readable_true_for_existing_directory(tmp_path: Path) -> None:
    """A real, accessible directory passes the readiness check."""
    assert is_readable(tmp_path) is True


def test_is_readable_false_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    assert is_readable(missing) is False


def test_is_readable_false_for_file_not_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "file.md"
    file_path.write_text("not a directory")
    assert is_readable(file_path) is False


def test_is_readable_does_not_raise_on_permission_error(tmp_path: Path) -> None:
    """A path that exists but rejects iterdir must fold into False, not raise."""

    class RaisingPath:
        def exists(self) -> bool:
            return True

        def is_dir(self) -> bool:
            return True

        def iterdir(self) -> object:
            raise PermissionError("simulated EACCES")

    # type: ignore[arg-type] — this fake conforms to the duck-typed surface
    # is_readable actually uses (exists, is_dir, iterdir).
    assert is_readable(RaisingPath()) is False  # type: ignore[arg-type]


def test_is_readable_handles_non_empty_directory(tmp_path: Path) -> None:
    """The early-break on iterdir() must work even when the dir has contents."""
    (tmp_path / "page.md").write_text("# hello")
    (tmp_path / "subdir").mkdir()
    assert is_readable(tmp_path) is True
