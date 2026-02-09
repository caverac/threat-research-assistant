"""Query endpoint for the research assistant."""

from fastapi import APIRouter, Request

from api.dependencies import get_research_chain
from core.schemas import QueryRequest, QueryResponse

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query_assistant(request: Request, query_request: QueryRequest) -> QueryResponse:
    """Ask the research assistant a question about OT threats."""
    chain = get_research_chain(request)
    return chain.run(query_request)
