from __future__ import annotations

import hashlib
import re

from .models import Chunk, PageText


def _normalise_for_chunking(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunk_id(document: str, page: int, chunk_index: int, text: str) -> str:
    payload = f"{document}|{page}|{chunk_index}|{text}".encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def chunk_pages(
    pages: list[PageText],
    chunk_size: int = 1200,
    overlap: int = 180,
    min_chunk_chars: int = 80,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size.")

    chunks: list[Chunk] = []
    for page in pages:
        text = _normalise_for_chunking(page.text)
        if not text:
            continue

        start = 0
        chunk_index = 0
        while start < len(text):
            hard_end = min(start + chunk_size, len(text))
            end = hard_end

            if hard_end < len(text):
                # Prefer a sentence/word boundary near the target size.
                lower_bound = start + max(int(chunk_size * 0.65), 1)
                candidates = [
                    text.rfind(". ", lower_bound, hard_end),
                    text.rfind("; ", lower_bound, hard_end),
                    text.rfind(" ", lower_bound, hard_end),
                ]
                boundary = max(candidates)
                if boundary > start:
                    end = boundary + 1

            chunk_text = text[start:end].strip()
            if len(chunk_text) >= min_chunk_chars or (start == 0 and end == len(text)):
                chunks.append(
                    Chunk(
                        id=_chunk_id(page.document, page.page, chunk_index, chunk_text),
                        document=page.document,
                        page=page.page,
                        chunk_index=chunk_index,
                        text=chunk_text,
                    )
                )
                chunk_index += 1

            if end >= len(text):
                break
            start = max(end - overlap, start + 1)

    return chunks
