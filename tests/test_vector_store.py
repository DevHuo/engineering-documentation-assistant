import unittest

import numpy as np

from src.models import Chunk
from src.vector_store import InMemoryVectorStore


class VectorStoreTests(unittest.TestCase):
    def test_cosine_search_ranks_expected_chunk_first(self):
        chunks = [
            Chunk(id="a", document="a.pdf", page=1, chunk_index=0, text="network"),
            Chunk(id="b", document="b.pdf", page=2, chunk_index=0, text="sensor"),
        ]
        embeddings = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        store = InMemoryVectorStore()
        store.upsert(chunks, embeddings)
        hits = store.search(np.asarray([0.95, 0.05], dtype=np.float32), top_k=2)
        self.assertEqual(hits[0].document, "a.pdf")
        self.assertEqual(hits[0].source_id, "S1")
        self.assertGreater(hits[0].score, hits[1].score)


if __name__ == "__main__":
    unittest.main()
