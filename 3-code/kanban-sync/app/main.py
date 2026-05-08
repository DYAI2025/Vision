"""FastAPI application entry point for kanban-sync.

Obsidian Kanban file I/O + sync-vs-edit boundary detection.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal, cast

from bearer_auth import (
    AcceptedTokens,
    AuthError,
    CallingIdentity,
    require_bearer_auth,
)
from bearer_auth.dependency import auth_error_to_response
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi import status as http_status
from pydantic import BaseModel
from starlette.responses import Response as StarletteResponse

from app import __version__
from app.board import add_card_to_board, load_board
from app.kanban import is_writable, kanban_subtree, load_card, save_card
from app.models import BoardState, CardRecord
from app.sync import sync_board


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.bearer_auth_verifier = AcceptedTokens(["operator"]).build_verifier()
    yield


app = FastAPI(
    title="kanban-sync",
    description="Obsidian Kanban file I/O + sync-vs-edit boundary detection.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


AuthDep = Annotated[CallingIdentity, Depends(require_bearer_auth)]


@app.exception_handler(AuthError)
async def auth_exception_handler(_request: Request, exc: AuthError) -> StarletteResponse:
    return cast(StarletteResponse, auth_error_to_response(exc))


class HealthResponse(BaseModel):
    """Shape per api-design.md § Health and observability."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


@app.get(
    "/v1/health",
    response_model=HealthResponse,
    tags=["health"],
    responses={
        200: {"description": "Kanban subtree mounted and writable; component ready."},
        503: {"description": "Kanban subtree missing, not a directory, or not writable."},
    },
)
async def health(response: Response) -> HealthResponse:
    kanban_ok = is_writable(kanban_subtree())
    if not kanban_ok:
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if kanban_ok else "degraded",
        version=__version__,
        checks={"kanban_subtree": "ok" if kanban_ok else "down"},
    )


# --- Card Endpoints ---

@app.post(
    "/v1/cards",
    status_code=http_status.HTTP_201_CREATED,
    tags=["cards"],
)
async def post_card(card: CardRecord, _identity: AuthDep) -> dict[str, str]:
    """Create or update a card file and add it to the board."""
    save_card(card)
    add_card_to_board(card.card_id, column_name=card.column or "Inbox")
    return {"card_id": card.card_id}


@app.get(
    "/v1/cards/{card_id}",
    response_model=CardRecord,
    tags=["cards"],
)
async def get_card(card_id: str, _identity: AuthDep) -> CardRecord:
    card = load_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


# --- Board Endpoints ---

@app.get(
    "/v1/boards/project-steering",
    response_model=BoardState,
    tags=["boards"],
)
async def get_board_state(_identity: AuthDep) -> BoardState:
    return load_board()


# --- Sync Endpoints ---

@app.post(
    "/v1/sync",
    tags=["sync"],
)
async def post_sync(identity: AuthDep) -> dict[str, Any]:
    """Trigger a sync run to detect manual changes in Obsidian."""
    return await sync_board(actor_id=identity.name)
