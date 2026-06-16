from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from support_triage.evaluation import evaluate_rules  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run support ticket triage evaluation.")
    parser.add_argument("--mode", choices=["rules"], required=True)
    parser.add_argument("--dataset", help="Path to a labeled triage dataset JSON file.")
    args = parser.parse_args()

    if args.mode == "rules":
        summary = evaluate_rules(dataset_path=args.dataset)
        _print_summary(summary)
        return 0

    return 1


def _print_summary(summary) -> None:
    print("Rule Baseline Evaluation")
    print("========================")
    print(f"dataset: {summary.dataset_path}")
    for name, value in summary.metrics().items():
        if name == "total_cases":
            print(f"{name}: {value}")
        else:
            print(f"{name}: {value:.3f}")

    print(f"failures: {len(summary.failures)}")
    if not summary.failures:
        return

    print()
    print("Representative Failures")
    print("-----------------------")
    for failure in summary.failures[:5]:
        print(f"- {failure.id}: {failure.subject}")
        print(f"  mismatched_fields: {', '.join(failure.mismatched_fields)}")
        print(f"  expected: {failure.expected}")
        print(f"  predicted: {failure.predicted}")


if __name__ == "__main__":
    raise SystemExit(main())
