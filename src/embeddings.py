from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from openai import OpenAI


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        if not api_key:
            raise ValueError("An OpenAI API key is required for embeddings.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed_texts(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = list(texts[start : start + batch_size])
            response = self.client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in response.data)

        matrix = np.asarray(vectors, dtype=np.float32)
        return _l2_normalise(matrix)

    def embed_query(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(model=self.model, input=text)
        vector = np.asarray(response.data[0].embedding, dtype=np.float32)
        return _l2_normalise(vector.reshape(1, -1))[0]


def _l2_normalise(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return matrix
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms
