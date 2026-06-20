from app.services.chunking import chunk_text


def test_chunk_text_short_returns_single_chunk():
    assert chunk_text("hello world", size=512, overlap=64) == ["hello world"]


def test_chunk_text_empty_returns_nothing():
    assert chunk_text("   ", size=512, overlap=64) == []


def test_chunk_text_splits_with_overlap():
    chunks = chunk_text("abcdefghij", size=4, overlap=1)
    assert chunks[0] == "abcd"
    assert chunks[1] == "defg"
    assert all(chunk.strip() for chunk in chunks)
