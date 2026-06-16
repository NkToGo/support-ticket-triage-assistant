from support_triage.evaluation import FailureRecord, evaluate_rules, load_eval_cases


METRIC_NAMES = (
    "category_accuracy",
    "priority_accuracy",
    "priority_within_one_accuracy",
    "routing_accuracy",
    "human_review_precision",
    "human_review_recall",
    "human_review_f1",
    "critical_priority_recall",
    "exact_match_accuracy",
)


def test_load_eval_cases_returns_valid_dataset() -> None:
    cases = load_eval_cases()

    assert len(cases) == 40
    assert all(case.id for case in cases)
    assert all(case.ticket.subject for case in cases)
    assert all(case.expected.rationale == "Expected label placeholder." for case in cases)


def test_load_eval_cases_accepts_custom_dataset_path() -> None:
    cases = load_eval_cases("data/eval/triage_holdout_cases.json")

    assert len(cases) == 24
    assert all(case.id for case in cases)


def test_rules_evaluation_returns_expected_total_cases() -> None:
    summary = evaluate_rules()

    assert summary.total_cases == 40
    assert summary.dataset_path.endswith("data\\eval\\triage_cases.json") or summary.dataset_path.endswith(
        "data/eval/triage_cases.json"
    )


def test_rules_evaluation_accepts_custom_dataset_path() -> None:
    summary = evaluate_rules(dataset_path="data/eval/triage_holdout_cases.json")

    assert summary.total_cases == 24
    assert summary.dataset_path.endswith(
        "data\\eval\\triage_holdout_cases.json"
    ) or summary.dataset_path.endswith("data/eval/triage_holdout_cases.json")


def test_rules_evaluation_metrics_are_bounded() -> None:
    summary = evaluate_rules()

    for metric_name in METRIC_NAMES:
        metric_value = getattr(summary, metric_name)
        assert 0.0 <= metric_value <= 1.0


def test_holdout_rules_evaluation_metrics_are_bounded() -> None:
    summary = evaluate_rules(dataset_path="data/eval/triage_holdout_cases.json")

    for metric_name in METRIC_NAMES:
        metric_value = getattr(summary, metric_name)
        assert 0.0 <= metric_value <= 1.0


def test_failure_records_include_mismatch_details() -> None:
    summary = evaluate_rules()

    if not summary.failures:
        return

    failure = summary.failures[0]
    assert isinstance(failure, FailureRecord)
    assert failure.id
    assert failure.subject
    assert failure.mismatched_fields
    assert failure.expected
    assert failure.predicted
    assert "category" in failure.expected
    assert "category" in failure.predicted
    assert isinstance(failure.expected_review_reasons, list)
    assert isinstance(failure.predicted_review_reasons, list)
