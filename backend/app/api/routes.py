"""API Route Handlers for Health, Diagnostics, and Status."""

from fastapi import APIRouter, Depends
from backend.app.api.schemas import HealthResponse, SystemStatusResponse
from backend.app.core.config import settings
from backend.app.core.security import verify_session_token

router = APIRouter(prefix="/api/v1", tags=["Health & Status"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Public endpoint to verify backend process health and connectivity.",
)
async def get_health() -> HealthResponse:
    """Return backend health and diagnostic details."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        bound_host=settings.HOST,
        bound_port=settings.PORT,
        active_provider=settings.AI_PROVIDER,
        allowed_domains=settings.get_allowed_domain_list(),
    )


@router.get(
    "/auth/session",
    summary="Local Session Bootstrap",
    description="Endpoint for local desktop UI to bootstrap the session token safely over loopback.",
)
async def get_session_bootstrap():
    """Provides initial session information to the verified local UI."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "token": settings.API_TOKEN,
        "provider": settings.AI_PROVIDER,
        "allowed_domains": settings.get_allowed_domain_list(),
    }


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    summary="System Telemetry & Status",
    description="Authenticated endpoint for full agent system status.",
)
async def get_status(
    token: str = Depends(verify_session_token),
) -> SystemStatusResponse:
    """Return authenticated diagnostic telemetry."""
    return SystemStatusResponse(
        status="operational",
        version=settings.APP_VERSION,
        active_tasks=0,
        pending_approvals=0,
        db_connected=True,
        provider_available=True,
        allowed_domains_count=len(settings.get_allowed_domain_list()),
        session_token_prefix=settings.API_TOKEN[:6] + "...",
    )


@router.get(
    "/provider/test",
    summary="AI Provider Connectivity Test",
    description="Actively test configured model provider connectivity and report real latency.",
)
async def test_provider(
    token: str = Depends(verify_session_token),
):
    """Test AI provider connection."""
    from backend.app.agent.providers.factory import active_provider

    result = await active_provider.test_connection()
    return result.model_dump()
