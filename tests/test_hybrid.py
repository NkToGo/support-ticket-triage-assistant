import pytest

from support_triage import hybrid
from support_triage.models import (
    HybridStrategy,
    ReviewReason,
    RoutingTarget,
    TicketCategory,
    TicketInput,
    TicketPriority,
    TriageResult,
)


def _result(
    *,
    category: TicketCategory = TicketCategory.TECHNICAL_SUPPORT,
    priority: TicketPriority = TicketPriority.P2,
    routing_target: RoutingTarget = RoutingTarget.SUPPORT_TIER_2,
    requires_human_review: bool = False,
    review_reasons: list[ReviewReason] | None = None,
    confidence: float = 0.82,
    rationale: str = "Fake LLM triage result.",
) -> TriageResult:
    return TriageResult(
        category=category,
        priority=priority,
        routing_target=routing_target,
        requires_human_review=requires_human_review,
        review_reasons=review_reasons or [],
        confidence=confidence,
        rationale=rationale,
    )


def test_high_confidence_non_sensitive_rules_result_does_not_call_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(ticket: TicketInput) -> TriageResult:
        raise AssertionError("LLM should not be called for this rules-only case.")

    monkeypatch.setattr(hybrid, "triage_with_llm", fail_if_called)

    result = hybrid.triage_with_hybrid(
        TicketInput(
            subject="Feature request",
            body="Would like dark mode added to the admin dashboard.",
        )
    )

    assert result.strategy == HybridStrategy.RULES_ONLY
    assert result.used_llm is False
    assert result.llm_result is None
    assert result.final_result == result.rules_result
    assert result.disagreement_fields == []


def test_unclear_rules_result_uses_fake_llm_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm_result = _result()
    calls = []

    def fake_llm(ticket: TicketInput) -> TriageResult:
        calls.append(ticket)
        return fake_llm_result

    monkeypatch.setattr(hybrid, "triage_with_llm", fake_llm)

    result = hybrid.triage_with_hybrid(
        TicketInput(subject="Need help", body="Call me back.")
    )

    assert len(calls) == 1
    assert result.strategy == HybridStrategy.RULES_THEN_LLM_FOR_UNCERTAIN
    assert result.used_llm is True
    assert result.llm_result == fake_llm_result
    assert result.final_result.category == TicketCategory.TECHNICAL_SUPPORT
    assert result.final_result.requires_human_review is True


def test_billing_sensitive_review_reason_triggers_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm_result = _result(
        category=TicketCategory.BILLING_SUBSCRIPTION,
        routing_target=RoutingTarget.BILLING_OPS,
        review_reasons=[ReviewReason.BILLING_SENSITIVE],
    )
    monkeypatch.setattr(hybrid, "triage_with_llm", lambda ticket: fake_llm_result)

    result = hybrid.triage_with_hybrid(
        TicketInput(
            subject="Refund duplicate invoice charge",
            body="We were charged twice for renewal and need a refund.",
        )
    )

    assert result.used_llm is True
    assert result.strategy == HybridStrategy.RULES_WITH_LLM_REVIEW_FOR_SENSITIVE_CASES
    assert ReviewReason.BILLING_SENSITIVE in result.rules_result.review_reasons


def test_customer_escalation_review_reason_triggers_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_llm_result = _result(
        category=TicketCategory.ACCOUNT_ACCESS,
        priority=TicketPriority.P1,
        routing_target=RoutingTarget.SUPPORT_TIER_2,
        requires_human_review=True,
        review_reasons=[
            ReviewReason.PRIORITY_HIGH,
            ReviewReason.CUSTOMER_ESCALATION,
        ],
    )
    monkeypatch.setattr(hybrid, "triage_with_llm", lambda ticket: fake_llm_result)

    result = hybrid.triage_with_hybrid(
        TicketInput(
            subject="Login escalation",
            body="The team owner is locked out and our executive sponsor asked us to escalate.",
        )
    )

    assert result.used_llm is True
    assert result.strategy == HybridStrategy.RULES_WITH_LLM_REVIEW_FOR_SENSITIVE_CASES
    assert ReviewReason.CUSTOMER_ESCALATION in result.rules_result.review_reasons


def test_disagreement_fields_are_populated_for_different_predictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        hybrid,
        "triage_with_llm",
        lambda ticket: _result(
            category=TicketCategory.FEATURE_REQUEST,
            priority=TicketPriority.P1,
            routing_target=RoutingTarget.PRODUCT_MANAGEMENT,
            requires_human_review=False,
            review_reasons=[],
        ),
    )

    result = hybrid.triage_with_hybrid(
        TicketInput(subject="Need help", body="Call me back.")
    )

    assert result.disagreement_fields == [
        "category",
        "priority",
        "routing_target",
        "requires_human_review",
        "review_reasons",
    ]


def test_final_result_requires_human_review_if_either_prediction_requires_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        hybrid,
        "triage_with_llm",
        lambda ticket: _result(requires_human_review=False),
    )

    result = hybrid.triage_with_hybrid(
        TicketInput(subject="Need help", body="Call me back.")
    )

    assert result.rules_result.requires_human_review is True
    assert result.llm_result is not None
    assert result.llm_result.requires_human_review is False
    assert result.final_result.requires_human_review is True


def test_higher_risk_priority_is_preserved_when_predictions_disagree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        hybrid,
        "triage_with_llm",
        lambda ticket: _result(
            priority=TicketPriority.P1,
            requires_human_review=False,
            review_reasons=[],
        ),
    )

    result = hybrid.triage_with_hybrid(
        TicketInput(subject="Need help", body="Call me back.")
    )

    assert result.rules_result.priority == TicketPriority.P3
    assert result.final_result.priority == TicketPriority.P1
    assert result.final_result.requires_human_review is True
    assert ReviewReason.PRIORITY_HIGH in result.final_result.review_reasons
