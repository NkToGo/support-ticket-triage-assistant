import pytest

from support_triage.evaluation import (
    FailureRecord,
    evaluate_hybrid,
    evaluate_llm,
    evaluate_rules,
    load_eval_cases,
)
from support_triage.llm import LLMTriageConfigurationError
from support_triage.models import HybridStrategy, HybridTriageResult, TicketCategory


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


def test_rules_evaluation_accepts_limit() -> None:
    summary = evaluate_rules(limit=5)

    assert summary.total_cases == 5
    for metric_name in METRIC_NAMES:
        metric_value = getattr(summary, metric_name)
        assert 0.0 <= metric_value <= 1.0


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


def test_llm_evaluation_uses_monkeypatched_predictor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = load_eval_cases()[:3]
    calls = []

    def fake_predictor(ticket):
        calls.append(ticket)
        return cases[len(calls) - 1].expected

    monkeypatch.setattr("support_triage.evaluation.triage_with_llm", fake_predictor)

    summary = evaluate_llm(cases=cases)

    assert summary.total_cases == 3
    assert summary.exact_match_accuracy == 1.0
    assert len(summary.failures) == 0
    assert calls == [case.ticket for case in cases]


def test_llm_evaluation_accepts_limit_with_fake_predictor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = load_eval_cases()
    calls = []

    def fake_predictor(ticket):
        calls.append(ticket)
        return cases[len(calls) - 1].expected

    monkeypatch.setattr("support_triage.evaluation.triage_with_llm", fake_predictor)

    summary = evaluate_llm(cases=cases, limit=2)

    assert summary.total_cases == 2
    assert len(calls) == 2


def test_llm_evaluation_missing_api_key_is_clear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LLMTriageConfigurationError, match="OPENAI_API_KEY"):
        evaluate_llm(limit=1)


def test_hybrid_evaluation_compares_final_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = load_eval_cases()[:1]
    expected = cases[0].expected

    wrong_rules_result = expected.model_copy(
        update={
            "category": TicketCategory.OTHER_UNCLEAR,
            "rationale": "Wrong wrapper result.",
        }
    )

    def fake_hybrid(ticket):
        return HybridTriageResult(
            final_result=expected,
            strategy=HybridStrategy.RULES_THEN_LLM_FOR_UNCERTAIN,
            rules_result=wrong_rules_result,
            llm_result=expected,
            used_llm=True,
            disagreement_fields=["category"],
            decision_rationale="Fake hybrid result for evaluation.",
        )

    monkeypatch.setattr("support_triage.evaluation.triage_with_hybrid", fake_hybrid)

    summary = evaluate_hybrid(cases=cases)

    assert summary.total_cases == 1
    assert summary.exact_match_accuracy == 1.0
    assert summary.failures == []
    assert summary.hybrid_used_llm_count == 1
    assert summary.hybrid_rules_only_count == 0
    assert summary.hybrid_disagreement_case_count == 1


def test_hybrid_evaluation_accepts_limit_and_counts_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = load_eval_cases()
    calls = []

    def fake_hybrid(ticket):
        index = len(calls)
        calls.append(ticket)
        expected = cases[index].expected
        used_llm = index == 1
        return HybridTriageResult(
            final_result=expected,
            strategy=(
                HybridStrategy.RULES_THEN_LLM_FOR_UNCERTAIN
                if used_llm
                else HybridStrategy.RULES_ONLY
            ),
            rules_result=expected,
            llm_result=expected if used_llm else None,
            used_llm=used_llm,
            disagreement_fields=["priority"] if used_llm else [],
            decision_rationale="Fake hybrid result for evaluation.",
        )

    monkeypatch.setattr("support_triage.evaluation.triage_with_hybrid", fake_hybrid)

    summary = evaluate_hybrid(cases=cases, limit=2)

    assert summary.total_cases == 2
    assert len(calls) == 2
    assert summary.hybrid_diagnostics() == {
        "hybrid_used_llm_count": 1,
        "hybrid_rules_only_count": 1,
        "hybrid_disagreement_case_count": 1,
    }


def test_hybrid_evaluation_missing_api_key_is_clear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LLMTriageConfigurationError, match="OPENAI_API_KEY"):
        evaluate_hybrid(limit=1)


@pytest.mark.parametrize("limit", [0, -1])
def test_evaluation_rejects_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit"):
        evaluate_rules(limit=limit)
