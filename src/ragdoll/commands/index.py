# ragdoll/commands/index.py

import sqlite3

from ragdoll.chunker import NaiveChunker
from ragdoll.config import SAVE_CHUNK_TEXT
from ragdoll.database.db_ops import mark_file_as_indexed
from ragdoll.embedder.providers import BaseEmbedder
from ragdoll.schemas import FileRecord


def index(
    file_record: FileRecord,
    db_conn: sqlite3.Connection,
    chunker: NaiveChunker,
    embedder: BaseEmbedder,
):
    """
    Processes a single file: reads, chunks, embeds, and saves to the database.

    Args:
        file_record: The FileRecord of the file to process.
        db_conn: An active database connection.
        chunker: An instance of NaiveChunker.
        embedder: An instance of an embedder class.
    """
    try:
        content = file_record.path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError) as e:
        print(f"\n[Warning] Could not read or decode file {file_record.path}: {e}")
        # Optionally, mark this file as "bad" in the DB so you don't retry it.
        # For now, we just skip it.
        return

    # 1. Chunk the content
    text_chunks = chunker.chunk(content)
    
    # If the file is empty or only whitespace, there might be no chunks.
    if not text_chunks:
        # We still mark it as indexed to clear the dirty flag.
        mark_file_as_indexed(db_conn, str(file_record.id), [], save_content=SAVE_CHUNK_TEXT)
        return

    # 2. Embed the chunks in a batch
    embeddings = embedder.embed_texts(text_chunks)

    # 3. Prepare data for the database
    #    The format is a list of (chunk_index, text_content, vector)
    chunk_data = [
        (idx, text, vec)
        for idx, (text, vec) in enumerate(zip(text_chunks, embeddings))
    ]

    # 4. Save to the database
    mark_file_as_indexed(
        conn=db_conn,
        file_id=str(file_record.id),
        chunks=chunk_data,
        save_content=SAVE_CHUNK_TEXT,
    )