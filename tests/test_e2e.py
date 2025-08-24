import pytest
import os
from pathlib import Path
import logging

# Import the command functions directly from main.py
from ragdoll.main import add, index, search, delete

# --- Constants and Test Setup ---
MOCK_DOCS_PATH = Path(__file__).parent / "data/mock-documents"

@pytest.fixture
def isolated_db(tmp_path):
    """
    Creates an isolated test environment with a clean database for each test run.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original_cwd)


@pytest.mark.e2e
def test_full_workflow_via_main_commands(isolated_db):
    """
    Tests the full user workflow by calling the command functions from main.py,
    using all real dependencies. It adds all documents, indexes them, and then
    runs a series of semantic search queries to verify each document can be
    correctly identified as the top result.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set. Skipping real API E2E test.")

    # --- 1. ADD & INDEX ---
    doc_files = list(MOCK_DOCS_PATH.glob("*.md"))
    assert doc_files, f"No mock documents found in {MOCK_DOCS_PATH}"

    logging.info(f"Calling main.add() for {len(doc_files)} files...")
    for doc_path in doc_files:
        add(path=doc_path.resolve())

    logging.info("Calling main.index() to process all dirty files...")
    index()

    search_test_cases = [
        ("A Basic Cyclopts Application", "00.md"),
        ("dlaczego zabawka dla dziecka źle uczy alfabetu?", "01.md"),
        ("rhcp song", "02.md"),
        ("What are the concerns with using the XFS filesystem on a desktop computer?", "03.md"),
        ("Jak działa trening 80/20 w kolarstwie?", "04.md"),
    ]

    # --- 3. EXECUTE & VERIFY SEARCHES ---
    logging.info(f"Executing {len(search_test_cases)} search verification tests...")

    for query, expected_filename in search_test_cases:
        logging.info(f'--> Testing Query: "{query}" | Expecting: "{expected_filename}"')
        
        # Call the search function and capture its return value
        search_response = search(query=query, limit=1)

        # Assertions
        assert search_response is not None, "The search function must return a response."
        assert search_response.results, f"Search for '{query}' returned no results."
        assert len(search_response.results) == 1, "Search should return exactly one result for limit=1"
        
        top_result = search_response.results[0]
        
        # The most important check: did we get the right document?
        assert top_result.path.name == expected_filename, \
            f"For query '{query}', expected '{expected_filename}' but got '{top_result.path.name}'"
        
        # Check that the score is a reasonable value
        assert isinstance(top_result.score, float)
        assert top_result.score > 0.3, f"Similarity score {top_result.score} is unexpectedly low for a targeted query."
        logging.info(f"    SUCCESS! Got '{top_result.path.name}' with score {top_result.score:.4f}")

    logging.info("All E2E searches completed successfully!")