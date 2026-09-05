from pathlib import Path

from docx import Document
from pypdf import PdfReader

from .chunker import Chunk, chunk_pages
from ..config import settings


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _load_pdf(path: Path) -> list[tuple[int | None, str]]:
    reader = PdfReader(str(path))
    pages: list[tuple[int | None, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append((i, text))
    return pages


def _load_docx(path: Path) -> list[tuple[int | None, str]]:
    doc = Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [(None, text)]


def _load_text(path: Path) -> list[tuple[int | None, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [(None, text)]


def load_document(path: str | Path) -> list[Chunk]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if suffix == ".pdf":
        pages = _load_pdf(file_path)
    elif suffix == ".docx":
        pages = _load_docx(file_path)
    else:
        pages = _load_text(file_path)

    return chunk_pages(
        pages=pages,
        source=file_path.name,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
