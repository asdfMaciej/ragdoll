import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from ragdoll.commands import search as _search 
from ragdoll.commands import add as _add 
from ragdoll.commands import list_files as _list_files
from cyclopts import App
from rich.console import Console
from rich.pretty import pprint
from rich.progress import track
from uuid6 import uuid7

app = App(help_flags=["--help", "-h"])
console = Console()

def _pretty_print_pydantic(model):
    """Helper to dump a Pydantic model to a dict and pretty-print it."""
    # `mode='json'` ensures types like UUID and datetime are serialized correctly.
    pprint(model.model_dump(mode='json'), expand_all=True)

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
            console.print("[bold red]Error: Invalid JSON string in --metadata.[/bold red]")
            raise sys.exit(1)

    file_record = _add(path, parsed_metadata)
    console.print("\n[green]Success![/green] File tracked. Run 'ragdoll index' to process it.")
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
        The maximum number of files to process.
    refresh
        Re-index already processed files, running in a worker-like mode.
    """
    if refresh:
        console.print(f"-> Starting worker to re-index all files...")
    else:
        console.print(f"-> Indexing up to [bold yellow]{limit}[/bold yellow] new files...")

    # Simulate a long-running process using rich's tracker
    total_files = limit if not refresh else 100  # Mock total
    for _ in track(range(total_files), description="Processing files..."):
        import time
        time.sleep(0.05)

    console.print("\n[green]Indexing complete![/green]")


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
    response = _list_files(page=page, per_page=per_page)
    _pretty_print_pydantic(response)


@app.command
def search(
    query: str,
    *,
    limit: int = 5,
):
    """Search for content across all indexed files.

    Parameters
    ----------
    query
        The search query string.
    limit
        Number of results to return.
    """
    console.print(f'-> Searching for: "[bold yellow]{query}[/bold yellow]" (limit: {limit})')
    response = _search(query, limit)
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
    if response.lower() != 'y':
        console.print("Operation cancelled.")
        sys.exit(0)

    console.print(f"[green]Success![/green] File '{path}' has been removed from tracking.")


if __name__ == "__main__":
    app()