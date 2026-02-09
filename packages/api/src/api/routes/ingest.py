"""Document ingestion endpoint."""

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.dependencies import get_embedding_client, get_vector_store
from core.schemas import Advisory, Incident, ThreatReport
from ingestion.chunker import TextChunker
from ingestion.parser import DocumentParser

router = APIRouter()


class IngestRequest(BaseModel):
    """Request body for document ingestion."""

    source_type: str
    document: dict[str, Any]


@router.post("")
async def ingest_document(request: Request, body: IngestRequest) -> dict:
    """Ingest a new threat intelligence document."""
    parser = DocumentParser()
    chunker = TextChunker()
    embedding_client = get_embedding_client(request)
    vector_store = get_vector_store(request)

    source_type = body.source_type
    document = body.document

    parsed: Advisory | ThreatReport | Incident
    if source_type == "advisory":
        parsed = parser.parse_advisory(document)
        chunks = chunker.chunk_advisory(parsed)
    elif source_type == "threat_report":
        parsed = parser.parse_threat_report(document)
        chunks = chunker.chunk_threat_report(parsed)
    elif source_type == "incident":
        parsed = parser.parse_incident(document)
        chunks = chunker.chunk_incident(parsed)
    else:
        return {"status": "error", "message": f"Unknown source_type: {source_type}"}

    for chunk in chunks:
        chunk.embedding = embedding_client.embed_text(chunk.content)
    vector_store.add(chunks)

    return {"status": "ok", "chunks_added": len(chunks), "source_id": parsed.id}
