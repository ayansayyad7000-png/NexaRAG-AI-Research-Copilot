import pytest

from nexarag.ingestion.chunker import chunk_text


def test_short_text_returns_one_chunk():
    text = " ".join(["linux"] * 50)
    chunks = chunk_text(text, source="notes.txt", chunk_size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0].source == "notes.txt"


def test_chunking_creates_overlap():
    words = [f"w{i}" for i in range(250)]
    chunks = chunk_text(
        " ".join(words),
        source="notes.txt",
        chunk_size=100,
        overlap=20,
    )
    assert len(chunks) >= 3
    first_words = chunks[0].text.split()
    second_words = chunks[1].text.split()
    assert first_words[-20:] == second_words[:20]


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text(
            "some text",
            source="x.txt",
            chunk_size=20,
            overlap=20,
        )
