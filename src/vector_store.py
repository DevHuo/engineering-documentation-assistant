from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .models import Chunk, SearchHit


class InMemoryVectorStore:
    """Small deterministic vector store used by unit tests and lightweight experiments."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._embeddings = np.empty((0, 0), dtype=np.float32)

    def reset(self) -> None:
        self._chunks = []
        self._embeddings = np.empty((0, 0), dtype=np.float32)

    def count(self) -> int:
        return len(self._chunks)

    def all_chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def upsert(self, chunks: Sequence[Chunk], embeddings: np.ndarray) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")

        self._chunks = list(chunks)
        self._embeddings = np.asarray(embeddings, dtype=np.float32)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[SearchHit]:
        if not self._chunks:
            return []

        query = np.asarray(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(query)

        if norm == 0:
            return []

        query = query / norm

        matrix = self._embeddings
        row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        row_norms[row_norms == 0] = 1.0
        matrix = matrix / row_norms

        scores = matrix @ query
        indexes = np.argsort(scores)[::-1][:top_k]

        return [
            SearchHit(
                source_id=f"S{rank + 1}",
                chunk_id=self._chunks[index].id,
                document=self._chunks[index].document,
                page=self._chunks[index].page,
                text=self._chunks[index].text,
                score=float(scores[index]),
            )
            for rank, index in enumerate(indexes)
        ]


class ChromaVectorStore:
    """Persistent cosine-similarity store backed by ChromaDB."""

    def __init__(self, path: str | Path, collection_name: str) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - dependency checked at runtime
            raise RuntimeError(
                "chromadb is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self._client = chromadb.PersistentClient(path=str(path))
        self._collection_name = collection_name

        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            # A fresh project may not yet have a collection.
            pass

        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return int(self._collection.count())

    def all_chunks(self) -> list[Chunk]:
        if self.count() == 0:
            return []

        result = self._collection.get(
            include=["documents", "metadatas"],
        )

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        return [
            Chunk(
                id=str(chunk_id),
                document=str(metadata["document"]),
                page=int(metadata["page"]),
                chunk_index=int(metadata["chunk_index"]),
                text=str(text),
            )
            for chunk_id, text, metadata in zip(
                ids,
                documents,
                metadatas,
                strict=True,
            )
        ]

    def upsert(self, chunks: Sequence[Chunk], embeddings: np.ndarray) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")

        if not chunks:
            return

        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=np.asarray(
                embeddings,
                dtype=np.float32,
            ).tolist(),
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "document": chunk.document,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> list[SearchHit]:
        if self.count() == 0:
            return []

        result = self._collection.query(
            query_embeddings=[
                np.asarray(
                    query_embedding,
                    dtype=np.float32,
                ).tolist()
            ],
            n_results=min(top_k, self.count()),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        hits: list[SearchHit] = []

        for rank, (
            chunk_id,
            text,
            metadata,
            distance,
        ) in enumerate(
            zip(
                ids,
                documents,
                metadatas,
                distances,
                strict=True,
            ),
            start=1,
        ):
            # With cosine distance, similarity is approximately 1 - distance.
            score = 1.0 - float(distance)

            hits.append(
                SearchHit(
                    source_id=f"S{rank}",
                    chunk_id=str(chunk_id),
                    document=str(metadata["document"]),
                    page=int(metadata["page"]),
                    text=str(text),
                    score=score,
                )
            )

        return hits