from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from support_triage.evaluation import evaluate_hybrid, evaluate_llm, evaluate_rules  # noqa: E402
from support_triage.llm import LLMTriageConfigurationError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run support ticket triage evaluation.")
    parser.add_argument("--mode", choices=["rules", "llm", "hybrid"], required=True)
    parser.add_argument("--dataset", help="Path to a labeled triage dataset JSON file.")
    parser.add_argument("--limit", type=int, help="Evaluate only the first N cases.")
    args = parser.parse_args()

    try:
        if args.mode == "rules":
            summary = evaluate_rules(dataset_path=args.dataset, limit=args.limit)
        elif args.mode == "llm":
            print("LLM mode may call the OpenAI API and requires OPENAI_API_KEY.")
            summary = evaluate_llm(dataset_path=args.dataset, limit=args.limit)
        else:
            print("Hybrid mode may call the OpenAI API when LLM review is needed.")
            summary = evaluate_hybrid(dataset_path=args.dataset, limit=args.limit)
    except LLMTriageConfigurationError as exc:
        print(f"{args.mode} evaluation failed: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 2

    _print_summary(summary, mode=args.mode, limit=args.limit)
    return 0


def _print_summary(summary, *, mode: str, limit: int | None) -> None:
    titles = {
        "rules": "Rule Baseline Evaluation",
        "llm": "LLM Triage Evaluation",
        "hybrid": "Hybrid Triage Evaluation",
    }
    title = titles[mode]
    print(title)
    print("=" * len(title))
    print(f"mode: {mode}")
    print(f"dataset: {summary.dataset_path}")
    if limit is not None:
        print(f"limit: {limit}")
    for name, value in summary.metrics().items():
        if name == "total_cases":
            print(f"{name}: {value}")
        else:
            print(f"{name}: {value:.3f}")

    for name, value in summary.hybrid_diagnostics().items():
        print(f"{name}: {value}")

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
