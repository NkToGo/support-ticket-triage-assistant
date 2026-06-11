from support_triage.models import (
    ReviewReason,
    RoutingTarget,
    TicketCategory,
    TicketInput,
    TicketPriority,
)
from support_triage.rules import triage_with_rules


def test_account_access_blocked_routes_to_tier_2_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Cannot sign in",
            body="I am locked out after MFA reset and blocked from work.",
        )
    )

    assert result.category == TicketCategory.ACCOUNT_ACCESS
    assert result.priority == TicketPriority.P1
    assert result.routing_target == RoutingTarget.SUPPORT_TIER_2
    assert result.requires_human_review is True
    assert ReviewReason.PRIORITY_HIGH in result.review_reasons


def test_billing_refund_triggers_billing_sensitive_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Refund duplicate invoice charge",
            body="We were charged twice for renewal and need a refund.",
        )
    )

    assert result.category == TicketCategory.BILLING_SUBSCRIPTION
    assert result.priority == TicketPriority.P2
    assert result.routing_target == RoutingTarget.BILLING_OPS
    assert result.requires_human_review is True
    assert ReviewReason.BILLING_SENSITIVE in result.review_reasons


def test_outage_becomes_p0_incident_response_and_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Application outage",
            body="The app is down for everyone on our whole team.",
        )
    )

    assert result.category == TicketCategory.PERFORMANCE_AVAILABILITY
    assert result.priority == TicketPriority.P0
    assert result.routing_target == RoutingTarget.INCIDENT_RESPONSE
    assert result.requires_human_review is True
    assert ReviewReason.PRIORITY_HIGH in result.review_reasons
    assert ReviewReason.POTENTIAL_INCIDENT in result.review_reasons


def test_feature_request_is_low_priority_product_management_no_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Feature request",
            body="Would like dark mode added to the admin dashboard.",
        )
    )

    assert result.category == TicketCategory.FEATURE_REQUEST
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.PRODUCT_MANAGEMENT
    assert result.requires_human_review is False
    assert result.review_reasons == []


def test_security_privacy_routes_to_security_compliance_and_requires_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Suspicious former employee access",
            body="A former employee still appears to have unauthorized access.",
        )
    )

    assert result.category == TicketCategory.DATA_SECURITY_PRIVACY
    assert result.routing_target == RoutingTarget.SECURITY_COMPLIANCE
    assert result.requires_human_review is True
    assert ReviewReason.SECURITY_OR_PRIVACY in result.review_reasons


def test_vague_ticket_is_unclear_and_requires_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Need help",
            body="Call me back.",
        )
    )

    assert result.category == TicketCategory.OTHER_UNCLEAR
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.SUPPORT_TIER_1
    assert result.requires_human_review is True
    assert ReviewReason.LOW_CONFIDENCE in result.review_reasons
    assert ReviewReason.MISSING_CRITICAL_DETAILS in result.review_reasons
