import json
import sys
from pathlib import Path
from typing import Optional
from ragdoll.commands import search as _search
from ragdoll.commands import add as _add
from ragdoll.commands import list_files as _list_files
from ragdoll.commands import delete as _delete
from ragdoll.commands import index as _index
from ragdoll.commands import preview as _preview
from cyclopts import App
from rich.console import Console
from rich.pretty import pprint
from rich.progress import track
from ragdoll.database import Database
from ragdoll.database.db_ops import get_dirty_files
from ragdoll.chunker import NaiveChunker
from ragdoll.embedder.get_embedder import get_embedder
from ragdoll.config import EMBEDDING_PROVIDER


app = App(help_flags=["--help", "-h"])
console = Console()


def _pretty_print_pydantic(model):
    """Helper to dump a Pydantic model to a dict and pretty-print it."""
    # `mode='json'` ensures types like UUID and datetime are serialized correctly.
    pprint(model.model_dump(mode="json", serialize_as_any=True), expand_all=True)


# --- CLI Commands ---


@app.command
def add(
    path: Path,
    *,
    metadata: Optional[str] = None,
):
    """Add a new file to the tracking index.

    Parameters
    ----------
    path
        The path to the file to add.
    metadata
        JSON string of metadata to attach. e.g., --metadata='{"id": "x-y-z"}'
    """
    if not path.exists() or not path.is_file():
        console.print(f"[bold red]Error: File not found at '{path}'[/bold red]")
        raise sys.exit(1)

    console.print(f"-> Adding file: [bold cyan]{path}[/bold cyan]")

    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
            console.print(f"  - With metadata: {parsed_metadata}")
        except json.JSONDecodeError:
            console.print(
                "[bold red]Error: Invalid JSON string in --metadata.[/bold red]"
            )
            raise sys.exit(1)

    file_record = _add(path, parsed_metadata)
    console.print(
        "\n[green]Success![/green] File tracked. Run 'ragdoll index' to process it."
    )
    _pretty_print_pydantic(file_record)


@app.command
def index(
    *,
    limit: int = 20,
    refresh: bool = False,
):
    """Process and index added files to make them searchable.

    Parameters
    ----------
    limit
        The maximum number of files to process in this run.
    refresh
        Run as a persistent worker to re-index files marked as dirty.
    """
    if refresh:
        # As requested, raise an error for the unimplemented worker mode.
        raise NotImplementedError(
            "The --refresh worker mode is not yet implemented."
        )

    console.print(
        f"-> Checking for up to [bold yellow]{limit}[/bold yellow] files to index..."
    )

    with Database() as db:
        # 1. Get the list of files that need processing.
        files_to_index = get_dirty_files(db.conn, limit=limit)

        if not files_to_index:
            console.print("[bold green]No new or changed files to index. All up to date![/bold green]")
            return

        console.print(f"-> Found [bold cyan]{len(files_to_index)}[/bold cyan] file(s) to process.")

        # 2. Set up the tools needed for processing.
        chunker = NaiveChunker(
            chunk_size=100,
            overlap=20
        )
        embedder = get_embedder(EMBEDDING_PROVIDER)

        # 3. Process each file, showing a progress bar.
        #    rich.track iterates over the list and displays progress automatically.
        for file_record in track(files_to_index, description="Processing files..."):
            _index(
                file_record=file_record,
                db_conn=db.conn,
                chunker=chunker,
                embedder=embedder,
            )

    console.print(f"\n[green]Indexing complete! Processed {len(files_to_index)} file(s).[/green]")


@app.command(name="list")
def list_files(
    page: int = 1,
    per_page: int = 20,
):
    """List all the files currently being tracked.

    Parameters
    ----------
    page
        Page number to retrieve.
    per_page
        Number of items per page.
    """
    # This now calls the real implementation
    response = _list_files(page=page, per_page=per_page)
    _pretty_print_pydantic(response)


@app.command
def preview(
    path: Path,
    *,
    show_embedding: bool = False,
):
    """Show detailed metadata and text chunks for a single file.

    Parameters
    ----------
    path
        The path of the file to preview.
    show_embedding
        Display the full embedding vector for each chunk.
    """
    console.print(f"-> Fetching preview for: [bold cyan]{path}[/bold cyan]")
    response = _preview(path)

    if not response:
        console.print(f"[bold red]Error: File not found in index at '{path}'[/bold red]")
        sys.exit(1)

    response_data = response.model_dump(mode="json")

    if not show_embedding:
        if 'chunks' in response_data and response_data['chunks']:
            for chunk in response_data['chunks']:
                embedding_list = chunk.get('embedding')
                if embedding_list:
                    summary = f"<{len(embedding_list)} dims> [{embedding_list[0]:.4f}, {embedding_list[1]:.4f}, ...]"
                    chunk['embedding'] = summary

    # 3. Pretty-print the (potentially modified) dictionary.
    pprint(response_data, expand_all=True)


@app.command
def search(
    query: str,
    *,
    limit: int = 5,
    with_chunks: bool = False,
):
    """Search for content across all indexed files.

    Results are ranked by the file's overall relevance.

    Parameters
    ----------
    query
        The search query string.
    limit
        Number of file results to return.
    with_chunks
        Include the specific matching text chunks in the results.
    """
    console.print(
        f'-> Searching for: "[bold yellow]{query}[/bold yellow]" (limit: {limit})'
    )

    response = _search(query, limit, with_chunks)
    print(response.results[0])

    console.print("\n[green]Found results:[/green]")
    _pretty_print_pydantic(response)


@app.command
def delete(
    path: Path,
):
    """Remove a file from the index.

    Parameters
    ----------
    path
        The path of the file to remove from tracking.
    """
    console.print(f"-> Preparing to delete tracking for: [bold red]{path}[/bold red]")

    response = input("Are you sure you want to delete this file from the index? [y/N] ")
    if response.lower() != "y":
        console.print("Operation cancelled.")
        sys.exit(0)

    rows_deleted = _delete(path)

    if rows_deleted > 0:
        console.print(
            f"\n[green]Success![/green] File '{path}' has been removed from the index."
        )
    else:
        console.print(
            f"\n[yellow]Info:[/yellow] File '{path}' was not found in the index. Nothing to do."
        )


if __name__ == "__main__":
    app()
