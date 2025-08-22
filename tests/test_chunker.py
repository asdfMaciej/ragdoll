from ragdoll.chunker import NaiveChunker
import pytest

def test_no_overlap():
    chunker = NaiveChunker(chunk_size=5, overlap=0)
    text = "abcdefghijk"
    chunks = chunker.chunk(text)
    assert chunks == ["abcde", "fghij", "k"]

def test_partial_overlap():
    chunker = NaiveChunker(chunk_size=4, overlap=2)
    text = "abcdefghij"
    chunks = chunker.chunk(text)
    assert chunks == ["abcd", "cdef", "efgh", "ghij"]

def test_chunk_size_larger_than_text():
    chunker = NaiveChunker(chunk_size=20, overlap=5)
    text = "short text"
    chunks = chunker.chunk(text)
    assert chunks == ["short text"]

def test_invalid_overlap_equal_to_chunk_size():
    with pytest.raises(ValueError):
        NaiveChunker(chunk_size=5, overlap=5)

def test_invalid_overlap_greater_than_chunk_size():
    with pytest.raises(ValueError):
        NaiveChunker(chunk_size=5, overlap=6)

def test_invalid_zero_chunk_size():
    with pytest.raises(ValueError):
        NaiveChunker(chunk_size=0, overlap=0)
