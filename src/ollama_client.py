from __future__ import annotations

import requests

from .config import settings


class OllamaError(RuntimeError):
    pass


def _url(path: str) -> str:
    return f"{settings.ollama_base_url.rstrip('/')}{path}"


def health_check(timeout: int = 3) -> bool:
    try:
        response = requests.get(_url("/api/version"), timeout=timeout)
        return response.ok
    except requests.RequestException:
        return False


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    try:
        response = requests.post(
            _url("/api/embed"),
            json={"model": settings.embed_model, "input": texts},
            timeout=180,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaError(
            "Could not generate embeddings. Make sure Ollama is running and "
            f"the model '{settings.embed_model}' is installed."
        ) from exc

    data = response.json()
    embeddings = data.get("embeddings")
    if not embeddings:
        raise OllamaError("Ollama returned no embeddings.")
    return embeddings


def chat(system_prompt: str, user_prompt: str) -> str:
    try:
        response = requests.post(
            _url("/api/chat"),
            json={
                "model": settings.chat_model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {"temperature": 0.2},
            },
            timeout=240,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaError(
            "Could not contact the local LLM. Make sure Ollama is running and "
            f"the model '{settings.chat_model}' is installed."
        ) from exc

    data = response.json()
    return data.get("message", {}).get("content", "").strip()
