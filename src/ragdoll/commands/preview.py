from pathlib import Path
from typing import Optional

from ragdoll.database import Database
from ragdoll.database.db_ops import get_chunks_for_file, get_file_by_path
from ragdoll.schemas import FilePreviewResponse


def preview(path: Path) -> Optional[FilePreviewResponse]:
    """
    Retrieves a file's metadata and all its associated text chunks.

    Returns:
        A FilePreviewResponse object if the file is found, otherwise None.
    """
    with Database() as db:
        file_record = get_file_by_path(db.conn, path)

        if not file_record:
            return None

        chunks = get_chunks_for_file(db.conn, str(file_record.id))

    # Combine the file record data and the chunk list into the response model
    response = FilePreviewResponse(
        **file_record.model_dump(),
        chunks=chunks
    )
    return response