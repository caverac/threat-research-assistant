"""Recommendation endpoint."""

from fastapi import APIRouter, Request

from core.schemas import Recommendation

router = APIRouter()


@router.get("/{user_id}", response_model=list[Recommendation])
async def get_recommendations(  # pylint: disable=unused-argument
    request: Request,
    user_id: str,
    max_results: int = 5,
) -> list[Recommendation]:
    """Get personalized recommendations for a user."""
    # For now, return top recommendations from the latest retrieval
    # In production, this would use user interaction history with get_research_chain(request)
    return []
