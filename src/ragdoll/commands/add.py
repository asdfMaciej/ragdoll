from ragdoll.schemas import FileRecord
from typing import Optional
from uuid6 import uuid7
from pathlib import Path


def add(path: Path, metadata: Optional[dict] = None) -> FileRecord:
    """Simulates adding a file to the database and returns a FileRecord."""
    # In a real app, you would calculate a real hash and save to a DB.
    file_record = FileRecord(
        id=uuid7(),
        path=path.resolve(),
        content_hash="sha256-mock-hash-value",
        metadata=metadata or {},
    )
    return file_record
