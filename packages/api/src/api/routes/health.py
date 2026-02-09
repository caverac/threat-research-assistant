"""Health check endpoint."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint with component status."""
    vector_store = request.app.state.vector_store
    return {
        "status": "healthy",
        "components": {
            "vector_store": {"status": "ok", "document_count": vector_store.count()},
            "reranker": {"status": "ok" if request.app.state.reranker else "not_loaded"},
        },
    }
