from pathlib import Path

from ragdoll.database import Database
from ragdoll.database.db_ops import delete_file_and_chunks, get_file_by_path


def delete(path: Path) -> int:
    """
    Deletes a file and its associated chunks from the database based on its path.

    Args:
        path: The path of the file to remove from tracking.

    Returns:
        The number of file records deleted (0 if the file was not found, 1 if it was).
    """
    with Database() as db:
        # First, we must find the file record to get its primary key (ID).
        file_to_delete = get_file_by_path(db.conn, path)

        if not file_to_delete:
            # If the file isn't tracked in the database, we can't delete anything.
            return 0

        # If the file exists, use its ID to delete it and all associated chunks.
        # The db_ops function will return the number of deleted file rows.
        rows_deleted = delete_file_and_chunks(db.conn, str(file_to_delete.id))
        return rows_deleted
