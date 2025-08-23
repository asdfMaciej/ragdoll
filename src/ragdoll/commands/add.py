from ragdoll.schemas import FileRecord
from typing import Optional
from uuid6 import uuid7
from pathlib import Path
from ragdoll.database import Database
from ragdoll.database.db_ops import add_or_update_file
import hashlib 


def add(path: Path, metadata: Optional[dict]) -> FileRecord:
    """
    Adds or updates a file in the database.

    This function calculates the file's content hash and then calls the
    database operation to either create a new record or update an existing
    one based on the file path.

    Args:
        path: The absolute path to the file.
        metadata: A dictionary of user-provided metadata.

    Returns:
        The resulting FileRecord from the database.
    """
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    # 2. Use the Database context manager to handle the connection.
    with Database() as db:
        # 3. Call the database operation to add or update the file record.
        #    The db_ops function handles the INSERT...ON CONFLICT logic.
        file_record = add_or_update_file(
            conn=db.conn,
            path=path,
            content_hash=content_hash,
            metadata=metadata,
        )

    return file_record