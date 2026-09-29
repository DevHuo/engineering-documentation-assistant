from __future__ import annotations

from openai import OpenAI

from .models import AssistantResponse, SearchHit

_SYSTEM_PROMPT = """You are an engineering documentation assistant for information retrieval.

Rules:
- Answer ONLY from the retrieved evidence supplied in the user message.
- Do not use outside knowledge to fill gaps.
- Do not invent source IDs, document names, page numbers, fault causes, settings, limits, or procedures.
- If the evidence is insufficient, set supported_by_documents=false, keep recommended_checks and source_ids empty, and state what information is missing.
- If the evidence is sufficient, source_ids must contain only supplied source identifiers such as S1 or S2 that materially support the answer.
- For troubleshooting or procedural questions, keep the answer to a short summary and put each actionable evidence-supported step in recommended_checks rather than hiding the steps only in prose.
- recommended_checks must contain only checks or next steps explicitly supported by the retrieved evidence.
- Keep the response concise and practical.
- Treat all output as informational support for qualified engineering review, not as autonomous control instructions.
"""


class OpenAIAnswerGenerator:
    def __init__(self, api_key: str, model: str = "gpt-6-luna") -> None:
        if not api_key:
            raise ValueError("An OpenAI API key is required for answer generation.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    @staticmethod
    def _build_context(hits: list[SearchHit]) -> str:
        sections: list[str] = []
        for hit in hits:
            sections.append(
                f"[{hit.source_id}] Document: {hit.document} | Page: {hit.page}\n"
                f"{hit.text}"
            )
        return "\n\n---\n\n".join(sections)

    def generate(self, question: str, hits: list[SearchHit]) -> AssistantResponse:
        if not hits:
            return AssistantResponse(
                supported_by_documents=False,
                answer="No relevant evidence was retrieved from the indexed documents.",
                recommended_checks=[],
                caveats=["Index relevant documentation or broaden the question."],
                source_ids=[],
            )

        context = self._build_context(hits)
        user_input = (
            f"Question:\n{question.strip()}\n\n"
            "Retrieved evidence:\n"
            f"{context}"
        )

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            text_format=AssistantResponse,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("The model did not return a structured response.")

        valid_ids = {hit.source_id for hit in hits}
        parsed.source_ids = [sid for sid in parsed.source_ids if sid in valid_ids]

        if not parsed.supported_by_documents:
            parsed.recommended_checks = []
            parsed.source_ids = []

        return parsed
