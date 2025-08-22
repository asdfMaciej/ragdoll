import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class FileRecord(BaseModel):
    """
    Represents a single file tracked by the system.
    """

    id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the file (UUIDv7 format).",
        examples=["0198d3b9-5a6d-7770-a4ab-ddacd32320b0"],
    )
    path: Path = Field(..., description="Absolute path to the file on disk.")
    indexed_at: Optional[datetime] = Field(
        None,
        description="Timestamp (UTC) when the file was last indexed. Null if never indexed.",
    )
    content_hash: str = Field(
        ...,
        description="SHA256 hash of the file content to detect changes.",
        examples=["ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"],
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="User-provided arbitrary metadata."
    )

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    """
    Represents pagination information for list responses.
    """

    page: int = Field(..., gt=0, description="The current page number.")
    per_page: int = Field(..., gt=0, description="Number of items per page.")
    page_count: int = Field(..., ge=0, description="Total number of pages available.")
    total_count: int = Field(
        ..., ge=0, description="Total number of items across all pages."
    )


class FileListResponse(BaseModel):
    """
    The response model for the `list` command.
    """

    files: List[FileRecord]
    pagination: Pagination


class SearchResult(FileRecord):
    """
    Represents a single search result, extending a FileRecord with a score.
    """

    score: float = Field(
        ...,
        description="The relevance score of the search result (higher is better).",
        examples=[0.93214],
    )


class SearchResponse(BaseModel):
    """
    The response model for the `search` command.
    """

    results: List[SearchResult]
    pagination: Optional[Pagination] = Field(
        None,
        description="Pagination for search results (often null for vector search).",
    )
