import math

from ragdoll.database import Database
from ragdoll.database.db_ops import get_paginated_files
from ragdoll.schemas import FileListResponse, Pagination


def list_files(page: int, per_page: int) -> FileListResponse:
    """
    Constructs a paginated list of all tracked files by fetching them from the database.
    """
    # 1. Use the Database context manager to connect.
    with Database() as db:
        # 2. Call the db_ops function to get real, complete file records and the total count.
        file_records, total_count = get_paginated_files(db.conn, page, per_page)

    # 3. Calculate pagination details.
    page_count = (
        math.ceil(total_count / per_page) if total_count > 0 else 0
    )
    if page > page_count and total_count > 0:
        page = page_count # Clamp page number to the last available page

    # 4. Assemble the final Pydantic response model.
    return FileListResponse(
        files=file_records,
        pagination=Pagination(
            page=page,
            per_page=per_page,
            page_count=page_count,
            total_count=total_count,
        ),
    )