from __future__ import annotations

from collections.abc import Iterable

from .chunking import chunk_pages
from .config import Settings
from .embeddings import OpenAIEmbeddingProvider
from .generation import OpenAIAnswerGenerator
from .models import AssistantResponse, SearchHit
from .pdf_loader import extract_pdf_bytes
from .retrieval import Retriever
from .vector_store import ChromaVectorStore


class DocumentationAssistantService:
    def __init__(self, settings: Settings) -> None:
        settings.require_api_key()

        self.settings = settings

        self.embedder = OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
        )

        self.store = ChromaVectorStore(
            path=settings.chroma_path,
            collection_name=settings.collection_name,
        )

        self.retriever = Retriever(
            self.embedder,
            self.store,
        )

        self.generator = OpenAIAnswerGenerator(
            api_key=settings.openai_api_key,
            model=settings.generation_model,
        )

    def reset_index(self) -> None:
        """
        Clear the persistent vector store and invalidate the
        retriever's cached lexical BM25 index.
        """
        self.store.reset()
        self.retriever.refresh()

    def index_documents(
        self,
        documents: Iterable[tuple[str, bytes]],
        *,
        reset: bool = True,
    ) -> dict[str, int]:
        """
        Extract, chunk, embed and index one or more PDF documents.

        The lexical BM25 index is refreshed after indexing so that
        subsequent hybrid retrieval uses the latest document corpus.
        """
        if reset:
            self.reset_index()

        total_pages = 0
        total_chunks = 0
        document_count = 0

        for document_name, pdf_bytes in documents:
            pages = extract_pdf_bytes(
                pdf_bytes,
                document_name,
            )

            chunks = chunk_pages(
                pages,
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            )

            if not chunks:
                continue

            embeddings = self.embedder.embed_texts(
                [
                    chunk.text
                    for chunk in chunks
                ]
            )

            self.store.upsert(
                chunks,
                embeddings,
            )

            document_count += 1
            total_pages += len(pages)
            total_chunks += len(chunks)

        # Rebuild the lexical BM25 index on the next retrieval.
        # This is required because the indexed corpus may have changed.
        self.retriever.refresh()

        return {
            "documents": document_count,
            "pages": total_pages,
            "chunks": total_chunks,
        }

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
    ) -> tuple[AssistantResponse, list[SearchHit]]:
        """
        Retrieve supporting passages and generate a grounded answer.
        """
        hits = self.retriever.retrieve(
            question,
            top_k=top_k or self.settings.top_k,
        )

        response = self.generator.generate(
            question,
            hits,
        )

        return response, hits