from __future__ import annotations

import math
import re
from collections import Counter
from typing import Protocol

from .models import Chunk, SearchHit

_TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+(?:[-_/.][A-Za-z0-9]+)*"
)

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "used",
    "what",
    "when",
    "where",
    "which",
    "with",
}


def _tokenize(text: str) -> list[str]:
    """
    Tokenise engineering text while preserving identifiers such as
    S7-1200, DC/DC/DC, PUT/GET and similar technical terms.

    Common English stopwords are removed so lexical ranking focuses
    more strongly on engineering terminology and exact identifiers.
    """
    tokens = [
        match.group(0).lower()
        for match in _TOKEN_PATTERN.finditer(text)
    ]

    return [
        token
        for token in tokens
        if token not in _STOPWORDS
    ]


class QueryEmbedder(Protocol):
    def embed_query(self, text: str): ...


class SearchableStore(Protocol):
    def search(
        self,
        query_embedding,
        top_k: int = 5,
    ) -> list[SearchHit]: ...

    def all_chunks(self) -> list[Chunk]: ...

    def count(self) -> int: ...


class _BM25Index:
    """
    Lightweight BM25 implementation for lexical retrieval.

    This complements dense embeddings when queries contain exact
    model identifiers, protocol names, technical parameters, or
    specialised engineering terminology.
    """

    def __init__(
        self,
        chunks: list[Chunk],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b

        self._tokens: list[list[str]] = [
            _tokenize(chunk.text)
            for chunk in chunks
        ]

        self._term_frequencies: list[Counter[str]] = [
            Counter(tokens)
            for tokens in self._tokens
        ]

        self._document_lengths = [
            len(tokens)
            for tokens in self._tokens
        ]

        self._average_document_length = (
            sum(self._document_lengths)
            / len(self._document_lengths)
            if self._document_lengths
            else 0.0
        )

        document_frequency: Counter[str] = Counter()

        for tokens in self._tokens:
            document_frequency.update(set(tokens))

        document_count = len(chunks)

        self._idf = {
            term: math.log(
                1.0
                + (
                    document_count
                    - frequency
                    + 0.5
                )
                / (
                    frequency
                    + 0.5
                )
            )
            for term, frequency in document_frequency.items()
        }

    def search(
        self,
        query: str,
        top_k: int,
    ) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []

        query_terms = set(_tokenize(query))

        if not query_terms:
            return []

        scored: list[tuple[int, float]] = []

        for index, term_frequency in enumerate(
            self._term_frequencies
        ):
            score = 0.0
            document_length = self._document_lengths[index]

            for term in query_terms:
                frequency = term_frequency.get(term, 0)

                if frequency == 0:
                    continue

                idf = self._idf.get(term, 0.0)

                denominator = (
                    frequency
                    + self.k1
                    * (
                        1.0
                        - self.b
                        + self.b
                        * document_length
                        / max(
                            self._average_document_length,
                            1.0,
                        )
                    )
                )

                score += (
                    idf
                    * frequency
                    * (self.k1 + 1.0)
                    / denominator
                )

            if score > 0:
                scored.append(
                    (
                        index,
                        score,
                    )
                )

        scored.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            (
                self.chunks[index],
                score,
            )
            for index, score in scored[:top_k]
        ]


class Retriever:
    """
    Hybrid engineering-document retriever.

    Combines:
      1. Dense semantic retrieval
      2. BM25 lexical retrieval
      3. Reciprocal Rank Fusion (RRF)
      4. Page-level result diversification

    The final SearchHit score is a normalised hybrid ranking score.
    It is not a probability or confidence value.
    """

    def __init__(
        self,
        embedder: QueryEmbedder,
        store: SearchableStore,
        *,
        dense_candidate_k: int = 50,
        lexical_candidate_k: int = 50,
        rrf_k: int = 60,
        max_chunks_per_page: int = 1,
    ) -> None:
        self.embedder = embedder
        self.store = store

        self.dense_candidate_k = dense_candidate_k
        self.lexical_candidate_k = lexical_candidate_k
        self.rrf_k = rrf_k
        self.max_chunks_per_page = max_chunks_per_page

        self._bm25: _BM25Index | None = None

    def refresh(self) -> None:
        """
        Invalidate the cached lexical index.

        The BM25 index will be rebuilt from the current vector-store
        corpus the next time a retrieval request is made.
        """
        self._bm25 = None

    def _get_bm25(self) -> _BM25Index:
        if self._bm25 is None:
            self._bm25 = _BM25Index(
                self.store.all_chunks()
            )

        return self._bm25

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[SearchHit]:
        question = question.strip()

        if not question:
            return []

        store_count = self.store.count()

        if store_count == 0:
            return []

        candidate_k = min(
            store_count,
            max(
                top_k * 10,
                self.dense_candidate_k,
                self.lexical_candidate_k,
            ),
        )

        # ---------------------------------------------------------
        # 1. Dense semantic retrieval
        # ---------------------------------------------------------

        query_embedding = self.embedder.embed_query(
            question
        )

        dense_hits = self.store.search(
            query_embedding,
            top_k=candidate_k,
        )

        # ---------------------------------------------------------
        # 2. BM25 lexical retrieval
        # ---------------------------------------------------------

        lexical_hits = self._get_bm25().search(
            question,
            top_k=candidate_k,
        )

        # ---------------------------------------------------------
        # 3. Reciprocal Rank Fusion
        # ---------------------------------------------------------

        fused_scores: dict[str, float] = {}
        hit_templates: dict[str, SearchHit] = {}

        for rank, hit in enumerate(
            dense_hits,
            start=1,
        ):
            fused_scores[hit.chunk_id] = (
                fused_scores.get(
                    hit.chunk_id,
                    0.0,
                )
                + 1.0
                / (
                    self.rrf_k
                    + rank
                )
            )

            hit_templates[hit.chunk_id] = hit

        for rank, (
            chunk,
            _lexical_score,
        ) in enumerate(
            lexical_hits,
            start=1,
        ):
            fused_scores[chunk.id] = (
                fused_scores.get(
                    chunk.id,
                    0.0,
                )
                + 1.0
                / (
                    self.rrf_k
                    + rank
                )
            )

            if chunk.id not in hit_templates:
                hit_templates[chunk.id] = SearchHit(
                    source_id="",
                    chunk_id=chunk.id,
                    document=chunk.document,
                    page=chunk.page,
                    text=chunk.text,
                    score=0.0,
                )

        ranked_chunk_ids = sorted(
            fused_scores,
            key=fused_scores.get,
            reverse=True,
        )

        if not ranked_chunk_ids:
            return []

        maximum_score = fused_scores[
            ranked_chunk_ids[0]
        ]

        # ---------------------------------------------------------
        # 4. Page-level diversification
        # ---------------------------------------------------------
        #
        # Multiple chunks from the same page should not consume the
        # full Top-k window. This increases source/page diversity and
        # gives the generation model broader relevant evidence.
        # ---------------------------------------------------------

        page_counts: Counter[
            tuple[str, int]
        ] = Counter()

        final_hits: list[SearchHit] = []

        for chunk_id in ranked_chunk_ids:
            template = hit_templates[
                chunk_id
            ]

            page_key = (
                template.document,
                template.page,
            )

            if (
                page_counts[page_key]
                >= self.max_chunks_per_page
            ):
                continue

            page_counts[page_key] += 1

            normalised_score = (
                fused_scores[chunk_id]
                / maximum_score
                if maximum_score
                else 0.0
            )

            final_hits.append(
                SearchHit(
                    source_id=(
                        f"S{len(final_hits) + 1}"
                    ),
                    chunk_id=template.chunk_id,
                    document=template.document,
                    page=template.page,
                    text=template.text,
                    score=normalised_score,
                )
            )

            if len(final_hits) >= top_k:
                break

        return final_hits