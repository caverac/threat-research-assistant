"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from api.dependencies import initialize_services, shutdown_services
from api.routes import health, ingest, query, recommend, reload


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize services on startup and clean up on shutdown."""
    initialize_services(app)
    yield
    shutdown_services(app)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="OT Threat Research Assistant",
        description="RAG-powered research assistant for ICS/OT threat intelligence",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(query.router, prefix="/query", tags=["query"])
    app.include_router(recommend.router, prefix="/recommendations", tags=["recommendations"])
    app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
    app.include_router(reload.router, prefix="/reload-index", tags=["reload"])

    return app
