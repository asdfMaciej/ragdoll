from collections import defaultdict
from typing import Dict

from ragdoll.database import Database
from ragdoll.database.db_ops import vector_search_raw_chunks
from ragdoll.embedder.get_embedder import get_embedder
from ragdoll.config import EMBEDDING_PROVIDER
from ragdoll.schemas import SearchResponse, SearchResult, ChunkSearchResult, FileRecord
from rich.console import Console


# Instantiate the console for logging
console = Console()
def search(query: str, limit: int, with_chunks: bool) -> SearchResponse:
    """
    Performs vector search, aggregates chunk results into files, and returns a final ranked list of files.
    """
    embedder = get_embedder(EMBEDDING_PROVIDER)
    query_vector = embedder.embed_text(query)

    with Database() as db:
        raw_chunk_limit = limit * 5
        raw_results = vector_search_raw_chunks(db.conn, query_vector, raw_chunk_limit)

    aggregated_results: Dict[str, SearchResult] = {}

    for chunk_res in raw_results:
        file_id = str(chunk_res.id)
        
        # This object holds the details for the specific chunk that matched
        matched_chunk = ChunkSearchResult(
            score=(1 - (chunk_res.distance / 2)),
            chunk_index=chunk_res.chunk_index,
            # Content is included here; Pydantic model can handle if it's None
            content=chunk_res.content,
        )

        if file_id not in aggregated_results:
            # First time we've seen a chunk from this file
            aggregated_results[file_id] = SearchResult(
                id=chunk_res.id,
                path=chunk_res.path,
                is_dirty=chunk_res.is_dirty,
                indexed_at=chunk_res.indexed_at,
                content_hash=chunk_res.content_hash,
                metadata=chunk_res.metadata,
                score=matched_chunk.score,
                # If with_chunks is True, start the list with the first chunk.
                # Otherwise, the field remains None.
                matched_chunks=[matched_chunk] if with_chunks else None,
            )
        else:
            # We have an existing entry for this file, so we update it
            result = aggregated_results[file_id]
            
            # Update the file's overall score to the highest score of its chunks
            result.score = max(result.score, matched_chunk.score)
            
            # If we are collecting chunks, append the new one.
            # The list is guaranteed to exist if with_chunks is True.
            if with_chunks:
                result.matched_chunks.append(matched_chunk)

    # Sort the aggregated file results by their final score, descending
    final_results = sorted(
        aggregated_results.values(), key=lambda r: r.score, reverse=True
    )
    
    # Return the top N results, wrapped in the response model
    return SearchResponse(results=final_results[:limit], pagination=None)