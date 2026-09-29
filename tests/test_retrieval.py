import unittest

from src.models import Chunk, SearchHit
from src.retrieval import Retriever


class FakeEmbedder:
    def embed_query(self, text: str):
        return [1.0, 0.0]


class FakeStore:
    def __init__(self):
        self.chunks = [
            Chunk(
                id="general",
                document="manual.pdf",
                page=10,
                chunk_index=0,
                text=(
                    "General communication overview and "
                    "network configuration."
                ),
            ),
            Chunk(
                id="put-get",
                document="manual.pdf",
                page=267,
                chunk_index=0,
                text=(
                    "PUT and GET instructions write and read "
                    "from a remote S7 CPU over a PROFINET "
                    "connection."
                ),
            ),
        ]

    def count(self):
        return len(self.chunks)

    def all_chunks(self):
        return list(self.chunks)

    def search(self, query_embedding, top_k=5):
        # Deliberately make the dense ranking imperfect.
        hits = [
            SearchHit(
                source_id="S1",
                chunk_id="general",
                document="manual.pdf",
                page=10,
                text=self.chunks[0].text,
                score=0.90,
            ),
            SearchHit(
                source_id="S2",
                chunk_id="put-get",
                document="manual.pdf",
                page=267,
                text=self.chunks[1].text,
                score=0.80,
            ),
        ]

        return hits[:top_k]


class DuplicatePageStore:
    def __init__(self):
        self.chunks = [
            Chunk(
                id="p1a",
                document="manual.pdf",
                page=1,
                chunk_index=0,
                text="network diagnostics alpha",
            ),
            Chunk(
                id="p1b",
                document="manual.pdf",
                page=1,
                chunk_index=1,
                text="network diagnostics beta",
            ),
            Chunk(
                id="p2a",
                document="manual.pdf",
                page=2,
                chunk_index=0,
                text="network diagnostics gamma",
            ),
        ]

    def count(self):
        return len(self.chunks)

    def all_chunks(self):
        return list(self.chunks)

    def search(self, query_embedding, top_k=5):
        hits = [
            SearchHit(
                source_id="S1",
                chunk_id="p1a",
                document="manual.pdf",
                page=1,
                text=self.chunks[0].text,
                score=0.99,
            ),
            SearchHit(
                source_id="S2",
                chunk_id="p1b",
                document="manual.pdf",
                page=1,
                text=self.chunks[1].text,
                score=0.98,
            ),
            SearchHit(
                source_id="S3",
                chunk_id="p2a",
                document="manual.pdf",
                page=2,
                text=self.chunks[2].text,
                score=0.97,
            ),
        ]
        return hits[:top_k]


class RetrievalTests(unittest.TestCase):
    def test_hybrid_retrieval_can_promote_exact_technical_match(self):
        retriever = Retriever(
            FakeEmbedder(),
            FakeStore(),
        )

        hits = retriever.retrieve(
            (
                "Which instructions write and read from "
                "a remote S7 CPU over PROFINET?"
            ),
            top_k=2,
        )

        self.assertEqual(hits[0].page, 267)
        self.assertEqual(hits[0].source_id, "S1")

    def test_page_diversification_limits_duplicate_page_chunks(self):
        retriever = Retriever(
            FakeEmbedder(),
            DuplicatePageStore(),
            max_chunks_per_page=1,
        )

        hits = retriever.retrieve(
            "network diagnostics",
            top_k=2,
        )

        self.assertEqual(len(hits), 2)
        self.assertEqual({hit.page for hit in hits}, {1, 2})


if __name__ == "__main__":
    unittest.main()
