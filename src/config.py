from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    generation_model: str = "gpt-6-luna"
    embedding_model: str = "text-embedding-3-small"
    chroma_path: Path = Path(".chroma")
    collection_name: str = "engineering_docs"
    chunk_size: int = 1200
    chunk_overlap: int = 180
    top_k: int = 5

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            generation_model=os.getenv("OPENAI_MODEL", "gpt-6-luna").strip(),
            embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ).strip(),
            chroma_path=Path(os.getenv("CHROMA_PATH", ".chroma")),
            collection_name=os.getenv("CHROMA_COLLECTION", "engineering_docs").strip(),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1200")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "180")),
            top_k=int(os.getenv("TOP_K", "5")),
        )

    def require_api_key(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
