from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from nexarag.ingestion.document_loader import SUPPORTED_EXTENSIONS
from nexarag.llm.ollama_client import OllamaError, health_check
from nexarag.rag.engine import RAGEngine


app = FastAPI(
    title="NexaRAG API",
    version="1.0.0",
    description="Local RAG API with Ollama and citation-grounded answers.",
)

engine = RAGEngine()


class AskRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "name": "NexaRAG AI Research Copilot",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "api": "ok",
        "ollama": health_check(),
        "indexed_chunks": len(engine.store.chunks),
    }


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    temp_dir = tempfile.TemporaryDirectory()
    paths: list[Path] = []

    try:
        for uploaded in files:
            suffix = Path(uploaded.filename or "").suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {suffix}",
                )

            safe_name = Path(uploaded.filename or f"document{suffix}").name
            path = Path(temp_dir.name) / safe_name
            path.write_bytes(await uploaded.read())
            paths.append(path)

        try:
            return engine.ingest(paths, reset=True)
        except (ValueError, OllamaError) as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        temp_dir.cleanup()


@app.post("/ask")
def ask(payload: AskRequest):
    try:
        return engine.ask(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.delete("/knowledge-base")
def clear_knowledge_base():
    engine.clear()
    return {"status": "cleared"}
