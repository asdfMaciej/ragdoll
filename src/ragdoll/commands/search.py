from ragdoll.schemas import SearchResponse, SearchResult
from uuid6 import uuid7 
from datetime import datetime
from pathlib import Path

def search(query: str, limit: int) -> SearchResponse:
    """Simulates performing a vector search and returning structured results."""
    # This would be a call to a vector database like ChromaDB, Weaviate, etc.
    mock_search_results = [
        SearchResult(
            id=uuid7(),
            path=Path("/path/to/file.md").resolve(),
            indexed_at=datetime.now(),
            content_hash="sha256-mock-hash-value",
            metadata={"id": "x-y-z"},
            score=0.93214,
        )
    ]
    return SearchResponse(results=mock_search_results, pagination=None)
