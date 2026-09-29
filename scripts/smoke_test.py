from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Settings
from src.service import DocumentationAssistantService


def main() -> None:
    base_settings = Settings.from_env()

    with TemporaryDirectory(prefix="engineering-doc-assistant-smoke-") as tmp_dir:
        settings = replace(
            base_settings,
            chroma_path=Path(tmp_dir) / "chroma",
            collection_name="smoke_test_docs",
        )
        service = DocumentationAssistantService(settings)

        demo_dir = ROOT / "demo_docs"
        documents = [
            (path.name, path.read_bytes())
            for path in sorted(demo_dir.glob("*.pdf"))
        ]
        stats = service.index_documents(documents, reset=True)
        print("Indexed:", stats)

        question = "What should be checked when controller communication times out?"
        response, hits = service.ask(question)
        print("\nQuestion:", question)
        print("Supported:", response.supported_by_documents)
        print("Answer:", response.answer)
        print("Checks:")
        for item in response.recommended_checks:
            print(" -", item)
        print("Sources:", response.source_ids)
        print("Retrieved:")
        for hit in hits:
            print(
                f" - {hit.source_id}: {hit.document} "
                f"p.{hit.page} ({hit.score:.3f})"
            )

        del service


if __name__ == "__main__":
    main()
