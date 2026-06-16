import json
from collections import Counter
from pathlib import Path

from support_triage.models import TicketCategory, TicketInput, TriageResult


DEFAULT_DATASET_PATH = Path("data/eval/triage_cases.json")
HOLDOUT_DATASET_PATH = Path("data/eval/triage_holdout_cases.json")
TOP_LEVEL_KEYS = {"id", "ticket", "expected", "notes"}
TICKET_KEYS = {"subject", "body", "customer_tier", "product_area"}
EXPECTED_KEYS = {
    "category",
    "priority",
    "routing_target",
    "requires_human_review",
    "review_reasons",
}


def test_default_eval_dataset_shape_and_labels_are_valid() -> None:
    _assert_dataset_is_valid(DEFAULT_DATASET_PATH, expected_cases=40, expected_per_category=5)


def test_holdout_eval_dataset_shape_and_labels_are_valid() -> None:
    _assert_dataset_is_valid(HOLDOUT_DATASET_PATH, expected_cases=24, expected_per_category=3)


def _assert_dataset_is_valid(
    dataset_path: Path,
    *,
    expected_cases: int,
    expected_per_category: int,
) -> None:
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))

    assert isinstance(cases, list)
    assert len(cases) == expected_cases

    ids: set[str] = set()
    category_counts: Counter[str] = Counter()

    for case in cases:
        assert set(case) == TOP_LEVEL_KEYS
        assert isinstance(case["id"], str)
        assert case["id"]
        assert case["id"] not in ids
        ids.add(case["id"])

        assert set(case["ticket"]) == TICKET_KEYS
        assert set(case["expected"]) == EXPECTED_KEYS

        TicketInput(**case["ticket"])
        TriageResult(
            **case["expected"],
            confidence=1.0,
            rationale="Dataset validation placeholder.",
        )
        category_counts[case["expected"]["category"]] += 1

    assert category_counts == Counter(
        {category.value: expected_per_category for category in TicketCategory}
    )
