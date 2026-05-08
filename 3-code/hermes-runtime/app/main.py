"""FastAPI application entry point for hermes-runtime.

Agent runtime for project-manager system.
Exposes semantic skills and agent lifecycle endpoints.
"""

from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from starlette.responses import Response as StarletteResponse

from app import __version__
from app.ollama_client import OllamaClient
from app.skills.extraction import ExtractionResult, extract_semantic_data
from app.orchestration import ProcessRequest, process_idea_to_proposal
from bearer_auth import (
    AcceptedTokens,
    AuthError,
    CallingIdentity,
    require_bearer_auth,
)
from bearer_auth.dependency import auth_error_to_response

app = FastAPI(
    title="hermes-runtime",
    description="Project-manager agent runtime for project-agent-system.",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

# Initialize auth verifier
accepted = AcceptedTokens(["operator", "frontend-workbench", "gbrain-bridge"])
app.state.bearer_auth_verifier = accepted.build_verifier()

# Initialize Ollama client
ollama = OllamaClient()


@app.exception_handler(AuthError)
async def auth_exception_handler(_request: Request, exc: AuthError) -> StarletteResponse:
    return auth_error_to_response(exc)


AuthDep = Annotated[CallingIdentity, Depends(require_bearer_auth)]


class HealthResponse(BaseModel):
    """Shape per api-design.md § Health and observability."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str]


@app.get("/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__, checks={})


class ExtractionRequest(BaseModel):
    text: str


@app.post(
    "/v1/extract",
    response_model=ExtractionResult,
    tags=["skills"],
)
async def post_extract(
    req: ExtractionRequest,
    _identity: AuthDep,
) -> ExtractionResult:
    """Run semantic extraction on the provided text using local AI."""
    try:
        return await extract_semantic_data(ollama, req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/process-idea",
    tags=["orchestration"],
)
async def post_process_idea(
    req: ProcessRequest,
    _identity: AuthDep,
) -> dict[str, Any]:
    """Process a raw idea text into a verifiable proposal and a Kanban card."""
    try:
        return await process_idea_to_proposal(ollama, req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
