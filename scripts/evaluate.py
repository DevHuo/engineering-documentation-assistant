from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Settings
from src.evaluation import evaluate_retrieval, load_cases
from src.service import DocumentationAssistantService


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval against labelled questions.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("evaluation/questions.json"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/results.csv"),
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    service = DocumentationAssistantService(settings)
    cases = load_cases(args.cases)
    results, summary = evaluate_retrieval(service.retriever, cases, top_k=args.top_k)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)

    print("Retrieval evaluation")
    print("--------------------")
    for key, value in summary.items():
        if key == "cases":
            print(f"{key}: {int(value)}")
        else:
            print(f"{key}: {value:.3f}")
    print(f"Detailed results: {args.output}")


if __name__ == "__main__":
    main()
