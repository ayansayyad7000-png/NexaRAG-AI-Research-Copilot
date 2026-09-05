from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .config import settings
from .document_loader import load_document
from .ollama_client import chat, embed_texts
from .vector_store import LocalVectorStore


SYSTEM_PROMPT = """You are NexaRAG, a careful research assistant.

Rules:
1. Answer using ONLY the supplied context.
2. If the context does not contain enough information, clearly say that the answer is not available in the indexed documents.
3. Cite claims using source numbers like [1], [2], [3].
4. Do not invent page numbers, facts, names, dates, or references.
5. Prefer a clear, structured answer.
6. When multiple sources disagree, mention the disagreement.
"""


class RAGEngine:
    def __init__(self):
        self.store = LocalVectorStore()

    def clear(self) -> None:
        self.store.clear()

    def ingest(self, paths: Iterable[str | Path], reset: bool = True) -> dict:
        if reset:
            self.clear()

        all_chunks = []
        files = []
        for path in paths:
            path = Path(path)
            chunks = load_document(path)
            all_chunks.extend(chunks)
            files.append(path.name)

        if not all_chunks:
            return {"files": files, "chunks": 0}

        batch_size = 32
        all_embeddings: list[list[float]] = []
        for start in range(0, len(all_chunks), batch_size):
            batch = all_chunks[start : start + batch_size]
            vectors = embed_texts([chunk.text for chunk in batch])
            all_embeddings.extend(vectors)

        self.store.add(all_chunks, all_embeddings)
        return {"files": files, "chunks": len(all_chunks)}

    def ask(self, question: str) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        if not self.store.chunks:
            raise ValueError("Knowledge base is empty. Upload and index documents first.")

        query_vector = embed_texts([question])[0]
        matches = self.store.search(query_vector, top_k=settings.top_k)
        context_parts = []
        sources = []

        for number, (chunk, score) in enumerate(matches, start=1):
            page_text = f", page {chunk.page}" if chunk.page else ""
            context_parts.append(f"[{number}] Source: {chunk.source}{page_text}\n{chunk.text}")
            sources.append({
                "id": number,
                "source": chunk.source,
                "page": chunk.page,
                "score": round(score, 4),
                "snippet": chunk.text[:500],
            })

        context = "\n\n".join(context_parts)
        prompt = f"""QUESTION:
{question}

CONTEXT:
{context}

Write the answer using only the context above. Use [1], [2], etc. citations.
"""
        answer = chat(SYSTEM_PROMPT, prompt)
        return {"question": question, "answer": answer, "sources": sources}
