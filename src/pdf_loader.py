from __future__ import annotations

import io
import re
from pathlib import Path

import pymupdf

from .models import PageText


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_bytes(pdf_bytes: bytes, document_name: str) -> list[PageText]:
    if not pdf_bytes:
        raise ValueError("PDF content is empty.")

    pages: list[PageText] = []
    with pymupdf.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as document:
        for index, page in enumerate(document):
            text = _clean_text(page.get_text("text"))
            if text:
                pages.append(
                    PageText(document=document_name, page=index + 1, text=text)
                )
    return pages


def extract_pdf_file(path: str | Path) -> list[PageText]:
    path = Path(path)
    return extract_pdf_bytes(path.read_bytes(), path.name)
