# ragdoll/db_ops.py

import json
import sqlite3
import struct
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid6 import uuid7

from ragdoll.schemas import FileRecord, SearchResult, ChunkRecord

# The dimension of the vector. This should match the Database class and your embedder.
EMBEDDING_DIM = 1024


def _vector_to_bytes(vector: List[float]) -> bytes:
    """Serializes a list of floats into bytes for sqlite-vec."""
    return struct.pack(f"{len(vector)}f", *vector)

def _bytes_to_vector(data: Optional[bytes]) -> Optional[List[float]]:
    """Deserializes bytes into a list of floats."""
    if not data:
        return None
    # Assuming the vector is stored as 4-byte floats (standard C float)
    num_floats = len(data) // 4
    return list(struct.unpack(f'{num_floats}f', data))


def _row_to_file_record(row: sqlite3.Row) -> FileRecord:
    """Converts a SQLite row to a FileRecord Pydantic model."""
    return FileRecord(
        id=row["id"],
        path=Path(row["path"]),
        is_dirty=bool(row["is_dirty"]),  # Convert integer back to boolean
        indexed_at=datetime.fromisoformat(row["indexed_at"]) if row["indexed_at"] else None,
        content_hash=row["content_hash"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
    )


def add_or_update_file(
    conn: sqlite3.Connection, path: Path, content_hash: str, metadata: Dict[str, Any]
) -> FileRecord:
    """
    Adds a new file to the database or updates it if the path already exists.

    If the file's content hash has changed, its `is_dirty` flag is set to true (1)
    to mark it for re-indexing. `indexed_at` is NOT modified here.

    Args:
        conn: The database connection.
        path: Absolute path to the file.
        content_hash: The SHA256 hash of the file's content.
        metadata: A dictionary of metadata to store.

    Returns:
        The created or updated FileRecord.
    """
    metadata_str = json.dumps(metadata)
    file_id = str(uuid7())
    path_str = str(path.resolve())

    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO files (id, path, content_hash, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                content_hash = excluded.content_hash,
                metadata = excluded.metadata,
                -- Set dirty flag if content has changed, otherwise keep existing state
                is_dirty = CASE
                    WHEN files.content_hash != excluded.content_hash THEN 1
                    ELSE files.is_dirty
                END;
            """,
            (file_id, path_str, content_hash, metadata_str),
        )

    # Fetch the complete record to return it
    row = conn.execute("SELECT * FROM files WHERE path = ?", (path_str,)).fetchone()
    return _row_to_file_record(row)


def get_file_by_path(conn: sqlite3.Connection, path: Path) -> Optional[FileRecord]:
    """Retrieves a file record by its path."""
    path_str = str(path.resolve())
    row = conn.execute("SELECT * FROM files WHERE path = ?", (path_str,)).fetchone()
    return _row_to_file_record(row) if row else None


def delete_file_and_chunks(conn: sqlite3.Connection, file_id: str) -> int:
    """
    Deletes a file and all its associated chunks from the database.

    Args:
        conn: The database connection.
        file_id: The unique ID of the file to delete.

    Returns:
        The number of file records deleted (should be 0 or 1).
    """
    with conn:
        # Chunks must be deleted first as they reference the file
        conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))

        # Execute the delete for the main file and get the row count
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        return cursor.rowcount


def get_dirty_files(conn: sqlite3.Connection, limit: int = 20) -> List[FileRecord]:
    """Retrieves a list of files that are marked as dirty and need indexing."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE is_dirty = 1 LIMIT ?", (limit,))
    rows = cursor.fetchall()
    return [_row_to_file_record(row) for row in rows]


def mark_file_as_indexed(
    conn: sqlite3.Connection,
    file_id: str,
    chunks: List[Tuple[int, str, List[float]]],
    save_content: bool = True,
):
    """
    Deletes old chunks, inserts new ones, and marks the file as 'not dirty'.

    This function should be called after chunks and embeddings have been generated.

    Args:
        conn: The database connection.
        file_id: The ID of the file the chunks belong to.
        chunks: A list of tuples, where each tuple is (chunk_index, text_content, vector).
        save_content: Whether to save the text content in the database.
    """
    with conn:
        # Clear any existing chunks for this file to handle re-indexing
        conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))

        # Prepare data for bulk insertion
        chunk_data = [
            (
                file_id,
                chunk_index,
                text_content if save_content else None,
                _vector_to_bytes(vector),
            )
            for chunk_index, text_content, vector in chunks
        ]

        # Insert new chunks
        if chunk_data:
            conn.executemany(
                "INSERT INTO chunks (file_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                chunk_data,
            )

        # Mark the parent file as indexed (not dirty) and update timestamp
        indexed_time = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE files SET indexed_at = ?, is_dirty = 0 WHERE id = ?",
            (indexed_time, file_id),
        )


def search_chunks(
    conn: sqlite3.Connection, query_vector: List[float], limit: int = 5
) -> List[SearchResult]:
    """
    Performs a vector search across all chunks.

    Args:
        conn: The database connection.
        query_vector: The embedding of the search query.
        limit: The maximum number of results to return.

    Returns:
        A list of SearchResult objects, sorted by relevance.
    """
    query_vector_bytes = _vector_to_bytes(query_vector)

    query = """
        SELECT
            f.id,
            f.path,
            f.is_dirty,
            f.indexed_at,
            f.content_hash,
            f.metadata,
            c.distance
        FROM chunks c
        JOIN files f ON c.file_id = f.id
        WHERE c.embedding MATCH ?
        ORDER BY c.distance
        LIMIT ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (query_vector_bytes, limit))
    rows = cursor.fetchall()

    results = []
    for row in rows:
        file_record = _row_to_file_record(row)
        score = 1 - (row["distance"] / 2) # Assumes cosine distance
        results.append(SearchResult(**file_record.model_dump(), score=score))

    return results

def get_paginated_files(
    conn: sqlite3.Connection, page: int, per_page: int
) -> Tuple[List[FileRecord], int]:
    """
    Retrieves a paginated list of all tracked files.

    Args:
        conn: The database connection.
        page: The page number to retrieve.
        per_page: The number of items per page.

    Returns:
        A tuple containing a list of FileRecord objects and the total count of all files.
    """
    offset = (page - 1) * per_page

    # First, get the total count of files for pagination metadata
    total_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]

    # Then, fetch the actual page of results
    query = "SELECT * FROM files ORDER BY id DESC LIMIT ? OFFSET ?"
    cursor = conn.cursor()
    cursor.execute(query, (per_page, offset))
    rows = cursor.fetchall()

    file_records = [_row_to_file_record(row) for row in rows]
    return file_records, total_count


def get_chunks_for_file(conn: sqlite3.Connection, file_id: str) -> List[ChunkRecord]:
    """
    Retrieves all text chunks and their embeddings associated with a specific file ID.

    Args:
        conn: The database connection.
        file_id: The ID of the file.

    Returns:
        A list of ChunkRecord objects.
    """
    query = "SELECT chunk_index, content, embedding FROM chunks WHERE file_id = ? ORDER BY chunk_index ASC"
    cursor = conn.cursor()
    cursor.execute(query, (file_id,))
    rows = cursor.fetchall()

    results = []
    for row in rows:
        data = dict(row)
        # Manually deserialize the embedding blob before validation
        data['embedding'] = _bytes_to_vector(data.get('embedding'))
        results.append(ChunkRecord.model_validate(data))
    
    return results