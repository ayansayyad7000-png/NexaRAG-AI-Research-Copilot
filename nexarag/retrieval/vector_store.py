from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ..ingestion.chunker import Chunk
from ..config import settings


class LocalVectorStore:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or settings.data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_path = self.data_dir / "embeddings.npy"
        self.metadata_path = self.data_dir / "chunks.json"
        self.embeddings: np.ndarray | None = None
        self.chunks: list[Chunk] = []
        self.load()

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def clear(self) -> None:
        self.embeddings = None
        self.chunks = []
        if self.embeddings_path.exists():
            self.embeddings_path.unlink()
        if self.metadata_path.exists():
            self.metadata_path.unlink()

    def save(self) -> None:
        if self.embeddings is None:
            return
        np.save(self.embeddings_path, self.embeddings)
        self.metadata_path.write_text(
            json.dumps([asdict(chunk) for chunk in self.chunks], indent=2),
            encoding="utf-8",
        )

    def load(self) -> None:
        if self.embeddings_path.exists() and self.metadata_path.exists():
            self.embeddings = np.load(self.embeddings_path)
            raw = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            self.chunks = [Chunk(**item) for item in raw]

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        matrix = np.asarray(embeddings, dtype=np.float32)
        matrix = self._normalize(matrix)

        if len(chunks) != len(matrix):
            raise ValueError("Number of chunks and embeddings must match.")

        if self.embeddings is None:
            self.embeddings = matrix
        else:
            if self.embeddings.shape[1] != matrix.shape[1]:
                raise ValueError(
                    "Embedding dimension changed. Clear the knowledge base and rebuild it."
                )
            self.embeddings = np.vstack([self.embeddings, matrix])

        self.chunks.extend(chunks)
        self.save()

    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[tuple[Chunk, float]]:
        if self.embeddings is None or not self.chunks:
            return []

        query = np.asarray(query_embedding, dtype=np.float32)
        query = self._normalize(query)[0]

        scores = self.embeddings @ query
        k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[::-1][:k]

        return [(self.chunks[i], float(scores[i])) for i in top_indices]
