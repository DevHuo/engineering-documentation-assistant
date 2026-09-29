from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _load(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {row["id"]: row for row in rows}


def _rank(reciprocal_rank: str) -> str:
    value = float(reciprocal_rank)
    if value == 0:
        return "MISS"
    return str(round(1 / value))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare case-level page ranks from two retrieval evaluation CSV files."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline-label", default="Dense")
    parser.add_argument("--candidate-label", default="Hybrid")
    args = parser.parse_args()

    baseline = _load(args.baseline)
    candidate = _load(args.candidate)

    common_ids = [case_id for case_id in baseline if case_id in candidate]
    if not common_ids:
        raise SystemExit("No matching case IDs were found between the two files.")

    print(f"{args.baseline_label} vs {args.candidate_label}")
    print("=" * 100)

    improved = 0
    worse = 0
    unchanged = 0

    for case_id in common_ids:
        base = baseline[case_id]
        cand = candidate[case_id]
        base_rr = float(base["page_reciprocal_rank"])
        cand_rr = float(cand["page_reciprocal_rank"])

        if cand_rr > base_rr:
            change = "IMPROVED"
            improved += 1
        elif cand_rr < base_rr:
            change = "WORSE"
            worse += 1
        else:
            change = "UNCHANGED"
            unchanged += 1

        print(
            f"{case_id:<16} "
            f"{args.baseline_label}={_rank(base['page_reciprocal_rank']):<5} "
            f"{args.candidate_label}={_rank(cand['page_reciprocal_rank']):<5} "
            f"{change:<10} "
            f"first_{args.baseline_label.lower()}={base['first_hit_page']} "
            f"first_{args.candidate_label.lower()}={cand['first_hit_page']}"
        )

    print("-" * 100)
    print(f"Improved: {improved} | Worse: {worse} | Unchanged: {unchanged}")


if __name__ == "__main__":
    main()
