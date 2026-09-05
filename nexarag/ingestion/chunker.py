from dataclasses import dataclass
from typing import Iterable


@dataclass
class Chunk:
    text: str
    source: str
    page: int | None = None
    chunk_id: str | None = None


def chunk_text(
    text: str,
    source: str,
    page: int | None = None,
    chunk_size: int = 180,
    overlap: int = 35,
) -> list[Chunk]:
    """Split text into overlapping word chunks."""
    clean = " ".join(text.split())
    if not clean:
        return []

    words = clean.split()
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    step = chunk_size - overlap
    chunks: list[Chunk] = []

    for index, start in enumerate(range(0, len(words), step)):
        part = words[start : start + chunk_size]
        if not part:
            continue
        if len(part) < 20 and chunks:
            chunks[-1].text = f"{chunks[-1].text} {' '.join(part)}"
            break

        chunks.append(
            Chunk(
                text=" ".join(part),
                source=source,
                page=page,
                chunk_id=f"{source}:{page or 0}:{index}",
            )
        )

        if start + chunk_size >= len(words):
            break

    return chunks


def chunk_pages(
    pages: Iterable[tuple[int | None, str]],
    source: str,
    chunk_size: int = 180,
    overlap: int = 35,
) -> list[Chunk]:
    output: list[Chunk] = []
    for page, text in pages:
        output.extend(
            chunk_text(
                text=text,
                source=source,
                page=page,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )
    return output
