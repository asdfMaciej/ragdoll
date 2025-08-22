from ragdoll.schemas import FileRecord, FileListResponse, Pagination
from uuid6 import uuid7
from datetime import datetime
from pathlib import Path


def list_files(page: int, per_page: int) -> FileListResponse:
    """Simulates fetching paginated file records from the database."""
    # This data would come from a database query in a real application.
    mock_db_records = [
        FileRecord(
            id=uuid7(),
            path=Path("/path/to/file.md").resolve(),
            indexed_at=None,
            content_hash="sha256-mock-hash-value",
            metadata={"id": "x-y-z"},
        ),
        FileRecord(
            id=uuid7(),
            path=Path("/path/to/another.txt").resolve(),
            indexed_at=datetime.now(),
            content_hash="sha256-another-hash",
            metadata={},
        ),
    ]
    return FileListResponse(
        files=mock_db_records,
        pagination=Pagination(
            page=page, per_page=per_page, page_count=1, total_count=2
        ),
    )
