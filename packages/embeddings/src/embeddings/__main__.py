"""CLI entry point for building the FAISS index from synthetic data."""

from core.config import Settings
from embeddings.client import BedrockEmbeddingClient
from embeddings.index import EmbeddingIndexer
from embeddings.store import FAISSVectorStore
from ingestion.chunker import TextChunker
from ingestion.loader import DataLoader
from ingestion.parser import DocumentParser


def main() -> None:
    """Load data, chunk, embed via Bedrock Titan, and save FAISS index."""
    settings = Settings()
    loader = DataLoader(settings)
    parser = DocumentParser()
    chunker = TextChunker(settings)

    print("Loading documents...")  # noqa: T201
    advisories = parser.parse_advisories(loader.load_advisories())
    reports = parser.parse_threat_reports(loader.load_threat_reports())
    incidents = parser.parse_incidents(loader.load_incidents())
    print(f"  {len(advisories)} advisories, {len(reports)} reports, {len(incidents)} incidents")  # noqa: T201

    print("Chunking documents...")  # noqa: T201
    chunks = []
    for advisory in advisories:
        chunks.extend(chunker.chunk_advisory(advisory))
    for report in reports:
        chunks.extend(chunker.chunk_threat_report(report))
    for incident in incidents:
        chunks.extend(chunker.chunk_incident(incident))
    print(f"  {len(chunks)} chunks")  # noqa: T201

    print("Embedding and indexing (this calls Bedrock Titan)...")  # noqa: T201
    embedding_client = BedrockEmbeddingClient(settings)
    store = FAISSVectorStore()
    indexer = EmbeddingIndexer(embedding_client, store)
    indexed = indexer.index_chunks(chunks, batch_size=10)
    print(f"  {indexed} chunks indexed")  # noqa: T201

    print(f"Saving FAISS index to {settings.faiss_index_path}...")  # noqa: T201
    store.save(settings.faiss_index_path)
    print("Done.")  # noqa: T201


if __name__ == "__main__":
    main()
