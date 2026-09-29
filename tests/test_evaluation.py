import unittest

from src.evaluation import RetrievalCase, evaluate_retrieval
from src.models import SearchHit


class FakeRetriever:
    def retrieve(self, question: str, top_k: int = 5):
        return [
            SearchHit(
                source_id="S1",
                chunk_id="x",
                document="wrong.pdf",
                page=1,
                text="x",
                score=0.9,
            ),
            SearchHit(
                source_id="S2",
                chunk_id="y",
                document="target.pdf",
                page=4,
                text="y",
                score=0.8,
            ),
        ][:top_k]


class MultiPositiveRetriever:
    def retrieve(self, question: str, top_k: int = 5):
        return [
            SearchHit(
                source_id="S1",
                chunk_id="a",
                document="target.pdf",
                page=246,
                text="relevant alternate page",
                score=0.9,
            ),
            SearchHit(
                source_id="S2",
                chunk_id="b",
                document="target.pdf",
                page=224,
                text="relevant primary page",
                score=0.8,
            ),
        ][:top_k]


class EvaluationTests(unittest.TestCase):
    def test_metrics(self):
        cases = [
            RetrievalCase(
                id="Q1",
                question="question",
                expected_document="target.pdf",
                expected_pages=(4,),
            )
        ]

        results, summary = evaluate_retrieval(
            FakeRetriever(),
            cases,
            top_k=2,
        )

        result = results[0]

        self.assertTrue(result.document_hit_at_k)
        self.assertFalse(result.page_hit_at_1)
        self.assertTrue(result.page_hit_at_3)
        self.assertTrue(result.page_hit_at_k)

        self.assertAlmostEqual(
            result.document_reciprocal_rank,
            0.5,
        )
        self.assertAlmostEqual(
            result.page_reciprocal_rank,
            0.5,
        )

        self.assertAlmostEqual(
            summary["document_recall@2"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["page_recall@1"],
            0.0,
        )
        self.assertAlmostEqual(
            summary["page_recall@3"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["page_recall@2"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["page_mrr"],
            0.5,
        )

    def test_any_expected_page_counts_as_positive(self):
        cases = [
            RetrievalCase(
                id="Q2",
                question="question",
                expected_document="target.pdf",
                expected_pages=(224, 246),
            )
        ]

        results, summary = evaluate_retrieval(
            MultiPositiveRetriever(),
            cases,
            top_k=2,
        )

        result = results[0]
        self.assertTrue(result.page_hit_at_1)
        self.assertAlmostEqual(result.page_reciprocal_rank, 1.0)
        self.assertAlmostEqual(summary["page_recall@1"], 1.0)


if __name__ == "__main__":
    unittest.main()
