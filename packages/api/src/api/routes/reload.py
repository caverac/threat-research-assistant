"""Index reload endpoint."""

from fastapi import APIRouter, Request

from api.dependencies import reload_index

router = APIRouter()


@router.post("")
async def reload_index_from_s3(request: Request) -> dict:
    """Re-download the FAISS index from S3 and replace the in-memory store."""
    previous, current = reload_index(request.app)
    return {
        "status": "ok",
        "previous_count": previous,
        "current_count": current,
    }
