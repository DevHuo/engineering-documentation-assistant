from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Settings
from src.service import DocumentationAssistantService


def main() -> None:
    parser = argparse.ArgumentParser(description="Index all PDF files in a folder.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--append", action="store_true", help="Do not reset the existing index.")
    args = parser.parse_args()

    paths = sorted(args.folder.glob("*.pdf"))
    if not paths:
        raise SystemExit(f"No PDF files found in {args.folder}")

    settings = Settings.from_env()
    service = DocumentationAssistantService(settings)
    stats = service.index_documents(
        ((path.name, path.read_bytes()) for path in paths),
        reset=not args.append,
    )
    print(stats)


if __name__ == "__main__":
    main()
