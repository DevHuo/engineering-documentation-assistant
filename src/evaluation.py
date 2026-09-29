from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import SearchHit


class RetrieverLike(Protocol):
    def retrieve(self, question: str, top_k: int = 5) -> list[SearchHit]: ...


@dataclass(frozen=True)
class RetrievalCase:
    id: str
    question: str
    expected_document: str
    expected_pages: tuple[int, ...]


@dataclass(frozen=True)
class CaseResult:
    id: str
    question: str
    document_hit_at_k: bool
    page_hit_at_1: bool
    page_hit_at_3: bool
    page_hit_at_k: bool
    document_reciprocal_rank: float
    page_reciprocal_rank: float
    first_hit_document: str | None
    first_hit_page: int | None


def load_cases(path: str | Path) -> list[RetrievalCase]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        RetrievalCase(
            id=item["id"],
            question=item["question"],
            expected_document=item["expected_document"],
            expected_pages=tuple(item["expected_pages"]),
        )
        for item in raw
    ]


def evaluate_retrieval(
    retriever: RetrieverLike,
    cases: list[RetrievalCase],
    top_k: int = 5,
) -> tuple[list[CaseResult], dict[str, float]]:
    results: list[CaseResult] = []

    for case in cases:
        hits = retriever.retrieve(case.question, top_k=top_k)

        document_ranks = [
            index + 1
            for index, hit in enumerate(hits)
            if hit.document == case.expected_document
        ]

        page_ranks = [
            index + 1
            for index, hit in enumerate(hits)
            if (
                hit.document == case.expected_document
                and hit.page in case.expected_pages
            )
        ]

        document_rr = (
            1.0 / document_ranks[0]
            if document_ranks
            else 0.0
        )

        page_rr = (
            1.0 / page_ranks[0]
            if page_ranks
            else 0.0
        )

        first = hits[0] if hits else None

        results.append(
            CaseResult(
                id=case.id,
                question=case.question,
                document_hit_at_k=bool(document_ranks),
                page_hit_at_1=any(rank <= 1 for rank in page_ranks),
                page_hit_at_3=any(rank <= 3 for rank in page_ranks),
                page_hit_at_k=bool(page_ranks),
                document_reciprocal_rank=document_rr,
                page_reciprocal_rank=page_rr,
                first_hit_document=first.document if first else None,
                first_hit_page=first.page if first else None,
            )
        )

    count = len(results) or 1

    summary = {
        f"document_recall@{top_k}":
            sum(r.document_hit_at_k for r in results) / count,
        "page_recall@1":
            sum(r.page_hit_at_1 for r in results) / count,
        "page_recall@3":
            sum(r.page_hit_at_3 for r in results) / count,
        f"page_recall@{top_k}":
            sum(r.page_hit_at_k for r in results) / count,
        "document_mrr":
            sum(r.document_reciprocal_rank for r in results) / count,
        "page_mrr":
            sum(r.page_reciprocal_rank for r in results) / count,
        "cases": float(len(results)),
    }

    return results, summary