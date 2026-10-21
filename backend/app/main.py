"""AitMate Agent Backend Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router as api_router
from backend.app.api.tasks_routes import router as tasks_router
from backend.app.api.notifications_routes import router as notifications_router
from backend.app.core.config import settings
from backend.app.storage.database import init_db

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aitmate.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and graceful shutdown."""
    logger.info("Initializing %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Server bound to %s:%d", settings.HOST, settings.PORT)
    logger.info("Initializing SQLite persistence layer...")
    init_db()
    logger.info("Configured AI Provider: %s", settings.AI_PROVIDER)
    logger.info("Active Domain Allowlist: %s", settings.get_allowed_domain_list())
    yield
    logger.info("Shutting down %s gracefully.", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local agent backend and policy enforcement service for AitMate desktop assistant.",
    lifespan=lifespan,
)

# Enforce strict local CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router)
app.include_router(tasks_router)
app.include_router(notifications_router)


@app.get("/", tags=["Root"])
async def root():
    """Friendly local landing endpoint."""
    return {
        "message": f"{settings.APP_NAME} Backend Running",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
