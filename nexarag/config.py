import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    chat_model: str = os.getenv("CHAT_MODEL", "qwen3:4b")
    embed_model: str = os.getenv("EMBED_MODEL", "embeddinggemma")
    top_k: int = int(os.getenv("TOP_K", "5"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "180"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "35"))
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))


settings = Settings()
