"""Typer application entry point for the `vision` CLI.

Skeleton task (TASK-cli-skeleton): exposes only `vision health` plus a
top-level `--version` flag. Subcommand groups (`vision source`, `vision
audit`, `vision rtbf`, `vision export`, `vision review`, `vision state`,
`vision backup`, `vision rotate`, `vision reconciliation`) are added by
the corresponding Phase 2-7 tasks via `cli.add_typer(...)`.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from app import __version__
from app.config import load_config
from app.health import gather_health, overall_status, to_json

cli = typer.Typer(
    name="vision",
    help="Operator CLI for project-agent-system.",
    no_args_is_help=True,
    add_completion=False,
)

stdout = Console()
stderr = Console(stderr=True)


def _print_version(value: bool) -> None:
    if value:
        stdout.print(f"vision {__version__}")
        raise typer.Exit(code=0)


@cli.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print the CLI version and exit.",
            callback=_print_version,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """`vision` — see `vision <subcommand> --help` for details."""


@cli.command("health")
def health_command(
    base_url: Annotated[
        str | None,
        typer.Option(
            "--base-url",
            help="Override VISION_BASE_URL for this invocation.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit a stable JSON document instead of a table."),
    ] = False,
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            help="Per-service request timeout in seconds.",
            min=0.5,
            max=60.0,
        ),
    ] = 5.0,
) -> None:
    """Aggregate `/v1/health/<service>` across all five backend services in parallel.

    Exit codes:
      0 — overall status is `ok`
      1 — overall status is `degraded` (mixture of ok + degraded; nothing unreachable)
      2 — overall status is `down` (at least one service is unreachable or down)
    """
    config = load_config(override_base_url=base_url)
    results = asyncio.run(gather_health(config, timeout=timeout))
    overall = overall_status(results)

    if json_output:
        stdout.print(to_json(results))
    else:
        table = Table(title=f"vision health  •  {config.base_url}", show_lines=False)
        table.add_column("Service", style="bold")
        table.add_column("Status")
        table.add_column("HTTP")
        table.add_column("Detail", overflow="fold")
        for r in results:
            color = {"ok": "green", "degraded": "yellow", "down": "red", "unreachable": "red"}[
                r.status
            ]
            http = "—" if r.http_status is None else str(r.http_status)
            table.add_row(r.service, f"[{color}]{r.status}[/{color}]", http, r.detail)
        stdout.print(table)
        stdout.print(f"\noverall: [bold]{overall}[/bold]")

    if overall == "down":
        sys.exit(2)
    if overall == "degraded":
        sys.exit(1)
    sys.exit(0)


def main() -> None:
    """Console-script entry point declared in `pyproject.toml`."""
    cli()


if __name__ == "__main__":
    main()
