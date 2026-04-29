"""Unit tests for app.config: env-driven base URL + token loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import DEFAULT_BASE_URL, load_config

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_load_config_returns_default_base_url_when_env_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("VISION_BASE_URL", raising=False)
    monkeypatch.delenv("OPERATOR_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.base_url == DEFAULT_BASE_URL
    assert config.operator_token is None


def test_load_config_reads_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VISION_BASE_URL", "https://vision.example.com/")
    monkeypatch.setenv("OPERATOR_TOKEN", "token-from-env")
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.base_url == "https://vision.example.com"  # trailing slash trimmed
    assert config.operator_token == "token-from-env"


def test_load_config_argument_overrides_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("VISION_BASE_URL", "https://from-env.example.com")
    monkeypatch.chdir(tmp_path)

    config = load_config(override_base_url="https://from-arg.example.com")

    assert config.base_url == "https://from-arg.example.com"


def test_load_config_reads_dotenv_when_env_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A `.env` in the cwd populates env vars when they're not already set."""
    monkeypatch.delenv("VISION_BASE_URL", raising=False)
    monkeypatch.delenv("OPERATOR_TOKEN", raising=False)
    (tmp_path / ".env").write_text(
        "VISION_BASE_URL=https://from-dotenv.example.com\nOPERATOR_TOKEN=token-from-dotenv\n"
    )
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.base_url == "https://from-dotenv.example.com"
    assert config.operator_token == "token-from-dotenv"


def test_load_config_explicit_env_wins_over_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If both `.env` and explicit env are set, explicit env wins."""
    monkeypatch.setenv("VISION_BASE_URL", "https://from-explicit-env.example.com")
    (tmp_path / ".env").write_text("VISION_BASE_URL=https://from-dotenv.example.com\n")
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.base_url == "https://from-explicit-env.example.com"


def test_load_config_walks_upward_to_find_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A `.env` in a parent directory is discovered when invoked from a subdir."""
    monkeypatch.delenv("VISION_BASE_URL", raising=False)
    (tmp_path / ".env").write_text("VISION_BASE_URL=https://from-parent-dotenv.example.com\n")
    subdir = tmp_path / "deep" / "nested"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)

    config = load_config()

    assert config.base_url == "https://from-parent-dotenv.example.com"


def test_load_config_treats_empty_token_as_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Empty string from env is treated as 'unset' rather than as a literal empty token."""
    monkeypatch.setenv("OPERATOR_TOKEN", "")
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.operator_token is None
