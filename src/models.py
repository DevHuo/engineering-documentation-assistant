from __future__ import annotations

from pydantic import BaseModel, Field


class PageText(BaseModel):
    document: str
    page: int = Field(ge=1)
    text: str


class Chunk(BaseModel):
    id: str
    document: str
    page: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str


class SearchHit(BaseModel):
    source_id: str
    chunk_id: str
    document: str
    page: int
    text: str
    score: float


class AssistantResponse(BaseModel):
    supported_by_documents: bool = Field(
        description="True only when the retrieved evidence supports the answer."
    )
    answer: str = Field(description="Concise answer grounded only in retrieved evidence.")
    recommended_checks: list[str] = Field(
        default_factory=list,
        description="Checks or next steps explicitly supported by the retrieved evidence.",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Important limitations, ambiguity, or missing information.",
    )
    source_ids: list[str] = Field(
        default_factory=list,
        description="Only source identifiers supplied in the retrieved context, e.g. S1, S2.",
    )
