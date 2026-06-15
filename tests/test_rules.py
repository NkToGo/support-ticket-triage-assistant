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


def test_routine_payment_failure_does_not_require_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Payment failed on renewal",
            body="The renewal payment failed because our card expired. Where can we update the payment method?",
        )
    )

    assert result.category == TicketCategory.BILLING_SUBSCRIPTION
    assert result.priority == TicketPriority.P2
    assert result.routing_target == RoutingTarget.BILLING_OPS
    assert result.requires_human_review is False
    assert result.review_reasons == []


def test_cancel_button_cosmetic_issue_is_bug_report_not_billing() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Button alignment looks off",
            body="The Save button is one pixel lower than the Cancel button. Everything still works.",
        )
    )

    assert result.category == TicketCategory.BUG_REPORT
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.ENGINEERING_TRIAGE
    assert result.requires_human_review is False


def test_high_impact_bug_report_is_high_priority() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Monthly report totals are wrong",
            body="The totals are wrong for all projects and finance is using this report today.",
        )
    )

    assert result.category == TicketCategory.BUG_REPORT
    assert result.priority == TicketPriority.P1
    assert result.routing_target == RoutingTarget.ENGINEERING_TRIAGE
    assert result.requires_human_review is True
    assert ReviewReason.PRIORITY_HIGH in result.review_reasons


def test_slight_slowness_without_blocked_users_is_low_priority() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Admin page slightly slow sometimes",
            body="The admin page is a little slow sometimes, but everything still works and no users are blocked.",
        )
    )

    assert result.category == TicketCategory.PERFORMANCE_AVAILABILITY
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.SUPPORT_TIER_1
    assert result.requires_human_review is False


def test_cross_customer_personal_data_export_is_p0_security_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Data exported to wrong customer",
            body="A scheduled export sent one customer's report to another customer and contained personal data.",
        )
    )

    assert result.category == TicketCategory.DATA_SECURITY_PRIVACY
    assert result.priority == TicketPriority.P0
    assert result.routing_target == RoutingTarget.SECURITY_COMPLIANCE
    assert result.requires_human_review is True
    assert ReviewReason.SECURITY_OR_PRIVACY in result.review_reasons
    assert ReviewReason.POLICY_SENSITIVE in result.review_reasons


def test_privacy_question_can_be_normal_priority_security_review() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="DPA and privacy handling question",
            body="Our legal team is reviewing the DPA and wants to confirm how personal data is handled.",
        )
    )

    assert result.category == TicketCategory.DATA_SECURITY_PRIVACY
    assert result.priority == TicketPriority.P2
    assert result.routing_target == RoutingTarget.SECURITY_COMPLIANCE
    assert result.requires_human_review is True
    assert ReviewReason.SECURITY_OR_PRIVACY in result.review_reasons
    assert ReviewReason.PRIORITY_HIGH not in result.review_reasons


def test_feature_request_with_import_wording_stays_feature_request() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Bulk user import enhancement",
            body="We would like a bulk user import option from CSV so onboarding large teams is faster.",
        )
    )

    assert result.category == TicketCategory.FEATURE_REQUEST
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.PRODUCT_MANAGEMENT
    assert result.requires_human_review is False


def test_multi_intent_ticket_missing_details_stays_unclear() -> None:
    result = triage_with_rules(
        TicketInput(
            subject="Billing, login, and errors",
            body="We have billing questions, login trouble, and some errors, but I need to gather examples before explaining.",
        )
    )

    assert result.category == TicketCategory.OTHER_UNCLEAR
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.SUPPORT_TIER_1
    assert result.requires_human_review is True
    assert ReviewReason.LOW_CONFIDENCE in result.review_reasons
    assert ReviewReason.MISSING_CRITICAL_DETAILS in result.review_reasons
