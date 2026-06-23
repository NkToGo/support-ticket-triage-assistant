import pytest
from pydantic import ValidationError

from support_triage.models import (
    CustomerTier,
    HybridStrategy,
    HybridTriageResult,
    ReviewReason,
    RoutingTarget,
    TicketCategory,
    TicketInput,
    TicketPriority,
    TriageResult,
)


def test_valid_ticket_input_can_be_created() -> None:
    ticket = TicketInput(
        subject="Cannot sign in",
        body="MFA is sending codes to an old phone.",
        customer_tier=CustomerTier.ENTERPRISE,
        product_area="authentication",
    )

    assert ticket.subject == "Cannot sign in"
    assert ticket.customer_tier == CustomerTier.ENTERPRISE


def test_valid_triage_result_can_be_created() -> None:
    result = TriageResult(
        category=TicketCategory.ACCOUNT_ACCESS,
        priority=TicketPriority.P1,
        routing_target=RoutingTarget.SUPPORT_TIER_2,
        requires_human_review=True,
        review_reasons=[ReviewReason.PRIORITY_HIGH],
        confidence=0.82,
        rationale="The customer cannot sign in because MFA is unavailable.",
    )

    assert result.category == TicketCategory.ACCOUNT_ACCESS
    assert result.requires_human_review is True
    assert result.review_reasons == [ReviewReason.PRIORITY_HIGH]


def test_valid_hybrid_triage_result_can_be_created() -> None:
    rules_result = TriageResult(
        category=TicketCategory.FEATURE_REQUEST,
        priority=TicketPriority.P3,
        routing_target=RoutingTarget.PRODUCT_MANAGEMENT,
        requires_human_review=False,
        review_reasons=[],
        confidence=0.85,
        rationale="Detected feature request or product feedback signals.",
    )

    result = HybridTriageResult(
        final_result=rules_result,
        strategy=HybridStrategy.RULES_ONLY,
        rules_result=rules_result,
        llm_result=None,
        used_llm=False,
        disagreement_fields=[],
        decision_rationale="Rules result accepted; no LLM review trigger was present.",
    )

    assert result.final_result == rules_result
    assert result.strategy == HybridStrategy.RULES_ONLY
    assert result.used_llm is False


def test_invalid_enum_values_fail_validation() -> None:
    with pytest.raises(ValidationError):
        TriageResult(
            category="not_a_category",
            priority=TicketPriority.P2,
            routing_target=RoutingTarget.SUPPORT_TIER_1,
            requires_human_review=False,
            review_reasons=[],
            confidence=0.5,
            rationale="The ticket can be handled by tier 1 support.",
        )
