import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from support_triage.llm import triage_with_llm
from support_triage.models import TicketInput, TicketPriority, TriageResult
from support_triage.rules import triage_with_rules


DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "eval" / "triage_cases.json"
EXPECTED_LABEL_PLACEHOLDER_RATIONALE = "Expected label placeholder."
PRIORITY_ORDER = {
    TicketPriority.P0: 0,
    TicketPriority.P1: 1,
    TicketPriority.P2: 2,
    TicketPriority.P3: 3,
}


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    ticket: TicketInput
    expected: TriageResult
    notes: str


@dataclass(frozen=True)
class FailureRecord:
    id: str
    subject: str
    expected: dict[str, Any]
    predicted: dict[str, Any]
    mismatched_fields: list[str]
    expected_review_reasons: list[str]
    predicted_review_reasons: list[str]


@dataclass(frozen=True)
class EvaluationSummary:
    dataset_path: str
    total_cases: int
    category_accuracy: float
    priority_accuracy: float
    priority_within_one_accuracy: float
    routing_accuracy: float
    human_review_precision: float
    human_review_recall: float
    human_review_f1: float
    critical_priority_recall: float
    exact_match_accuracy: float
    failures: list[FailureRecord]

    def metrics(self) -> dict[str, int | float]:
        return {
            "total_cases": self.total_cases,
            "category_accuracy": self.category_accuracy,
            "priority_accuracy": self.priority_accuracy,
            "priority_within_one_accuracy": self.priority_within_one_accuracy,
            "routing_accuracy": self.routing_accuracy,
            "human_review_precision": self.human_review_precision,
            "human_review_recall": self.human_review_recall,
            "human_review_f1": self.human_review_f1,
            "critical_priority_recall": self.critical_priority_recall,
            "exact_match_accuracy": self.exact_match_accuracy,
        }


def load_eval_cases(path: Path | str | None = None) -> list[EvaluationCase]:
    dataset_path = Path(path) if path is not None else DEFAULT_DATASET_PATH
    raw_cases = json.loads(dataset_path.read_text(encoding="utf-8"))

    cases: list[EvaluationCase] = []
    for raw_case in raw_cases:
        ticket = TicketInput(**raw_case["ticket"])
        expected = TriageResult(
            **raw_case["expected"],
            confidence=1.0,
            rationale=EXPECTED_LABEL_PLACEHOLDER_RATIONALE,
        )
        cases.append(
            EvaluationCase(
                id=raw_case["id"],
                ticket=ticket,
                expected=expected,
                notes=raw_case["notes"],
            )
        )

    return cases


def evaluate_rules(
    cases: Sequence[EvaluationCase] | None = None,
    dataset_path: Path | str | None = None,
    limit: int | None = None,
) -> EvaluationSummary:
    return _evaluate_with_predictor(
        triage_with_rules,
        cases=cases,
        dataset_path=dataset_path,
        limit=limit,
    )


def evaluate_llm(
    cases: Sequence[EvaluationCase] | None = None,
    dataset_path: Path | str | None = None,
    limit: int | None = None,
) -> EvaluationSummary:
    return _evaluate_with_predictor(
        triage_with_llm,
        cases=cases,
        dataset_path=dataset_path,
        limit=limit,
    )


def _evaluate_with_predictor(
    predictor: Callable[[TicketInput], TriageResult],
    *,
    cases: Sequence[EvaluationCase] | None = None,
    dataset_path: Path | str | None = None,
    limit: int | None = None,
) -> EvaluationSummary:
    if cases is not None and dataset_path is not None:
        raise ValueError("Pass either cases or dataset_path, not both.")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than zero.")

    if cases is not None:
        eval_cases = list(cases)
        summary_dataset_path = "provided cases"
    else:
        selected_dataset_path = Path(dataset_path) if dataset_path is not None else DEFAULT_DATASET_PATH
        eval_cases = load_eval_cases(selected_dataset_path)
        summary_dataset_path = str(selected_dataset_path.resolve())

    if limit is not None:
        eval_cases = eval_cases[:limit]

    total_cases = len(eval_cases)

    category_correct = 0
    priority_correct = 0
    priority_within_one = 0
    routing_correct = 0
    exact_matches = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    critical_expected = 0
    critical_predicted_correct = 0
    failures: list[FailureRecord] = []

    for case in eval_cases:
        predicted = predictor(case.ticket)
        expected = case.expected

        category_match = predicted.category == expected.category
        priority_match = predicted.priority == expected.priority
        routing_match = predicted.routing_target == expected.routing_target
        review_match = predicted.requires_human_review == expected.requires_human_review
        review_reasons_match = set(predicted.review_reasons) == set(expected.review_reasons)

        category_correct += int(category_match)
        priority_correct += int(priority_match)
        priority_within_one += int(_is_priority_within_one(predicted.priority, expected.priority))
        routing_correct += int(routing_match)
        exact_matches += int(
            category_match and priority_match and routing_match and review_match
        )

        if predicted.requires_human_review and expected.requires_human_review:
            true_positives += 1
        elif predicted.requires_human_review and not expected.requires_human_review:
            false_positives += 1
        elif not predicted.requires_human_review and expected.requires_human_review:
            false_negatives += 1

        if expected.priority in {TicketPriority.P0, TicketPriority.P1}:
            critical_expected += 1
            critical_predicted_correct += int(predicted.priority in {TicketPriority.P0, TicketPriority.P1})

        mismatched_fields = _mismatched_fields(
            category_match=category_match,
            priority_match=priority_match,
            routing_match=routing_match,
            review_match=review_match,
            review_reasons_match=review_reasons_match,
        )
        if mismatched_fields:
            failures.append(_build_failure_record(case, predicted, mismatched_fields))

    precision = _safe_divide(true_positives, true_positives + false_positives)
    recall = _safe_divide(true_positives, true_positives + false_negatives)

    return EvaluationSummary(
        dataset_path=summary_dataset_path,
        total_cases=total_cases,
        category_accuracy=_safe_divide(category_correct, total_cases),
        priority_accuracy=_safe_divide(priority_correct, total_cases),
        priority_within_one_accuracy=_safe_divide(priority_within_one, total_cases),
        routing_accuracy=_safe_divide(routing_correct, total_cases),
        human_review_precision=precision,
        human_review_recall=recall,
        human_review_f1=_f1(precision, recall),
        critical_priority_recall=_safe_divide(critical_predicted_correct, critical_expected),
        exact_match_accuracy=_safe_divide(exact_matches, total_cases),
        failures=failures,
    )


def _is_priority_within_one(predicted: TicketPriority, expected: TicketPriority) -> bool:
    return abs(PRIORITY_ORDER[predicted] - PRIORITY_ORDER[expected]) <= 1


def _mismatched_fields(
    *,
    category_match: bool,
    priority_match: bool,
    routing_match: bool,
    review_match: bool,
    review_reasons_match: bool,
) -> list[str]:
    fields = []
    if not category_match:
        fields.append("category")
    if not priority_match:
        fields.append("priority")
    if not routing_match:
        fields.append("routing_target")
    if not review_match:
        fields.append("requires_human_review")
    if not review_reasons_match:
        fields.append("review_reasons")
    return fields


def _build_failure_record(
    case: EvaluationCase,
    predicted: TriageResult,
    mismatched_fields: list[str],
) -> FailureRecord:
    expected = _labels_to_dict(case.expected)
    predicted_labels = _labels_to_dict(predicted)
    return FailureRecord(
        id=case.id,
        subject=case.ticket.subject,
        expected=expected,
        predicted=predicted_labels,
        mismatched_fields=mismatched_fields,
        expected_review_reasons=expected["review_reasons"],
        predicted_review_reasons=predicted_labels["review_reasons"],
    )


def _labels_to_dict(result: TriageResult) -> dict[str, Any]:
    return {
        "category": result.category.value,
        "priority": result.priority.value,
        "routing_target": result.routing_target.value,
        "requires_human_review": result.requires_human_review,
        "review_reasons": [reason.value for reason in result.review_reasons],
    }


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
