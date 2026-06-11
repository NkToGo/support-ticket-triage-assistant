import re
from collections.abc import Iterable

from support_triage.models import (
    CustomerTier,
    ReviewReason,
    RoutingTarget,
    TicketCategory,
    TicketInput,
    TicketPriority,
    TriageResult,
)


CATEGORY_KEYWORDS: dict[TicketCategory, tuple[str, ...]] = {
    TicketCategory.ACCOUNT_ACCESS: (
        "login",
        "log in",
        "sign in",
        "signin",
        "password",
        "mfa",
        "2fa",
        "sso",
        "locked out",
        "invite",
    ),
    TicketCategory.BILLING_SUBSCRIPTION: (
        "invoice",
        "charge",
        "refund",
        "cancel",
        "cancellation",
        "payment",
        "subscription",
        "renewal",
        "credit",
        "chargeback",
    ),
    TicketCategory.BUG_REPORT: (
        "broken",
        "error",
        "fails",
        "failed",
        "failure",
        "regression",
        "reproduce",
        "wrong",
        "expected",
        "actual",
        "500",
        "502",
    ),
    TicketCategory.PERFORMANCE_AVAILABILITY: (
        "outage",
        "down",
        "slow",
        "timeout",
        "unavailable",
        "latency",
        "503",
        "everyone",
        "whole team",
        "all users",
    ),
    TicketCategory.TECHNICAL_SUPPORT: (
        "setup",
        "set up",
        "configure",
        "configuration",
        "api key",
        "webhook",
        "permission",
        "permissions",
        "import",
        "export",
        "integration",
    ),
    TicketCategory.DATA_SECURITY_PRIVACY: (
        "security",
        "privacy",
        "gdpr",
        "suspicious",
        "breach",
        "leak",
        "leaked",
        "exposed",
        "delete data",
        "data deletion",
        "unauthorized",
        "former employee access",
    ),
    TicketCategory.FEATURE_REQUEST: (
        "feature request",
        "add",
        "improve",
        "suggestion",
        "would like",
        "enhancement",
        "dark mode",
    ),
}

CATEGORY_PRECEDENCE: tuple[TicketCategory, ...] = (
    TicketCategory.DATA_SECURITY_PRIVACY,
    TicketCategory.PERFORMANCE_AVAILABILITY,
    TicketCategory.BILLING_SUBSCRIPTION,
    TicketCategory.ACCOUNT_ACCESS,
    TicketCategory.BUG_REPORT,
    TicketCategory.TECHNICAL_SUPPORT,
    TicketCategory.FEATURE_REQUEST,
)

BROAD_IMPACT_KEYWORDS = (
    "all users",
    "everyone",
    "whole team",
    "entire team",
    "many users",
    "nobody",
    "company-wide",
)
OUTAGE_KEYWORDS = ("outage", "down", "unavailable", "503", "service unavailable")
DATA_RISK_KEYWORDS = (
    "breach",
    "leak",
    "leaked",
    "exposed",
    "data loss",
    "lost data",
)
ACCESS_BLOCKED_KEYWORDS = (
    "blocked",
    "locked out",
    "cannot access",
    "can't access",
    "cannot log in",
    "can't log in",
    "cannot sign in",
    "can't sign in",
    "unable to log in",
    "cannot get into",
)
BILLING_SENSITIVE_KEYWORDS = (
    "refund",
    "chargeback",
    "disputed charge",
    "cancellation",
    "cancel",
    "credit",
)
ESCALATION_KEYWORDS = (
    "escalation",
    "escalate",
    "legal",
    "churn",
    "cancel our contract",
    "executive",
)
POLICY_SENSITIVE_KEYWORDS = (
    "gdpr",
    "delete data",
    "data deletion",
    "data exposure",
    "exposed",
    "access to another user",
)
GENERIC_VAGUE_PHRASES = (
    "need help",
    "help me",
    "call me",
    "problem",
    "issue",
)


def triage_with_rules(ticket: TicketInput) -> TriageResult:
    text = _normalize_text(ticket.subject, ticket.body)
    matched_categories = _matched_categories(text)
    category = _choose_category(matched_categories)
    vague = _is_vague(text, matched_categories)
    if vague:
        category = TicketCategory.OTHER_UNCLEAR

    priority = _choose_priority(text, category, ticket.customer_tier, vague)
    routing_target = _choose_routing_target(text, category, priority)
    confidence = _choose_confidence(text, category, priority, matched_categories, vague)
    review_reasons = _choose_review_reasons(
        text=text,
        category=category,
        priority=priority,
        confidence=confidence,
        matched_categories=matched_categories,
        vague=vague,
    )

    return TriageResult(
        category=category,
        priority=priority,
        routing_target=routing_target,
        requires_human_review=bool(review_reasons),
        review_reasons=review_reasons,
        confidence=confidence,
        rationale=_build_rationale(text, category, vague),
    )


def _normalize_text(*parts: str) -> str:
    joined = " ".join(parts)
    return re.sub(r"\s+", " ", joined.lower()).strip()


def _matched_categories(text: str) -> set[TicketCategory]:
    return {
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if _has_any(text, keywords)
    }


def _choose_category(matched_categories: set[TicketCategory]) -> TicketCategory:
    for category in CATEGORY_PRECEDENCE:
        if category in matched_categories:
            return category
    return TicketCategory.OTHER_UNCLEAR


def _choose_priority(
    text: str,
    category: TicketCategory,
    customer_tier: CustomerTier | None,
    vague: bool,
) -> TicketPriority:
    if vague or category == TicketCategory.FEATURE_REQUEST:
        return TicketPriority.P3

    if _is_p0(text, category):
        return TicketPriority.P0

    if (
        category == TicketCategory.DATA_SECURITY_PRIVACY
        or _has_any(text, ACCESS_BLOCKED_KEYWORDS)
        or _has_any(text, ("blocked core workflow", "cannot work", "blocked from work"))
        or customer_tier in {CustomerTier.PREMIUM, CustomerTier.ENTERPRISE}
    ):
        return TicketPriority.P1

    return TicketPriority.P2


def _choose_routing_target(
    text: str,
    category: TicketCategory,
    priority: TicketPriority,
) -> RoutingTarget:
    if category == TicketCategory.ACCOUNT_ACCESS:
        if _has_any(text, ACCESS_BLOCKED_KEYWORDS):
            return RoutingTarget.SUPPORT_TIER_2
        return RoutingTarget.SUPPORT_TIER_1

    if category == TicketCategory.BILLING_SUBSCRIPTION:
        return RoutingTarget.BILLING_OPS
    if category == TicketCategory.BUG_REPORT:
        return RoutingTarget.ENGINEERING_TRIAGE
    if category == TicketCategory.PERFORMANCE_AVAILABILITY:
        if priority in {TicketPriority.P0, TicketPriority.P1}:
            return RoutingTarget.INCIDENT_RESPONSE
        return RoutingTarget.SUPPORT_TIER_1
    if category == TicketCategory.TECHNICAL_SUPPORT:
        return RoutingTarget.SUPPORT_TIER_2
    if category == TicketCategory.DATA_SECURITY_PRIVACY:
        return RoutingTarget.SECURITY_COMPLIANCE
    if category == TicketCategory.FEATURE_REQUEST:
        return RoutingTarget.PRODUCT_MANAGEMENT
    return RoutingTarget.SUPPORT_TIER_1


def _choose_confidence(
    text: str,
    category: TicketCategory,
    priority: TicketPriority,
    matched_categories: set[TicketCategory],
    vague: bool,
) -> float:
    if vague:
        return 0.60
    if len(matched_categories) > 1:
        return 0.70
    if (
        priority == TicketPriority.P0
        or category == TicketCategory.DATA_SECURITY_PRIVACY
        or _has_any(text, OUTAGE_KEYWORDS)
    ):
        return 0.90
    if category in {
        TicketCategory.BILLING_SUBSCRIPTION,
        TicketCategory.BUG_REPORT,
        TicketCategory.TECHNICAL_SUPPORT,
    }:
        return 0.80
    return 0.85


def _choose_review_reasons(
    text: str,
    category: TicketCategory,
    priority: TicketPriority,
    confidence: float,
    matched_categories: set[TicketCategory],
    vague: bool,
) -> list[ReviewReason]:
    reasons: list[ReviewReason] = []

    if confidence < 0.75:
        _add_reason(reasons, ReviewReason.LOW_CONFIDENCE)
    if len(matched_categories) > 1:
        _add_reason(reasons, ReviewReason.AMBIGUOUS_CATEGORY)
    if priority in {TicketPriority.P0, TicketPriority.P1}:
        _add_reason(reasons, ReviewReason.PRIORITY_HIGH)
    if category == TicketCategory.DATA_SECURITY_PRIVACY:
        _add_reason(reasons, ReviewReason.SECURITY_OR_PRIVACY)
    if _has_any(text, BILLING_SENSITIVE_KEYWORDS):
        _add_reason(reasons, ReviewReason.BILLING_SENSITIVE)
    if _has_any(text, OUTAGE_KEYWORDS) or (
        category == TicketCategory.PERFORMANCE_AVAILABILITY
        and _has_any(text, BROAD_IMPACT_KEYWORDS)
    ):
        _add_reason(reasons, ReviewReason.POTENTIAL_INCIDENT)
    if _has_any(text, ESCALATION_KEYWORDS):
        _add_reason(reasons, ReviewReason.CUSTOMER_ESCALATION)
    if vague:
        _add_reason(reasons, ReviewReason.MISSING_CRITICAL_DETAILS)
    if _has_any(text, POLICY_SENSITIVE_KEYWORDS):
        _add_reason(reasons, ReviewReason.POLICY_SENSITIVE)

    return reasons


def _build_rationale(text: str, category: TicketCategory, vague: bool) -> str:
    if vague:
        return "Ticket details are too limited to route confidently."
    if category == TicketCategory.DATA_SECURITY_PRIVACY:
        return "Detected security/privacy and sensitive-data signals."
    if category == TicketCategory.PERFORMANCE_AVAILABILITY:
        if _has_any(text, BROAD_IMPACT_KEYWORDS):
            return "Detected outage and broad-impact signals."
        return "Detected availability or performance signals."
    if category == TicketCategory.BILLING_SUBSCRIPTION:
        if _has_any(text, BILLING_SENSITIVE_KEYWORDS):
            return "Detected billing-sensitive refund, cancellation, charge, or credit signals."
        return "Detected billing or subscription signals."
    if category == TicketCategory.ACCOUNT_ACCESS:
        if _has_any(text, ACCESS_BLOCKED_KEYWORDS):
            return "Detected account access and blocked-login signals."
        return "Detected account access signals."
    if category == TicketCategory.BUG_REPORT:
        return "Detected broken behavior or error signals."
    if category == TicketCategory.TECHNICAL_SUPPORT:
        return "Detected setup or configuration support signals."
    if category == TicketCategory.FEATURE_REQUEST:
        return "Detected feature request or product feedback signals."
    return "No strong triage signals were detected."


def _is_p0(text: str, category: TicketCategory) -> bool:
    if _has_any(text, DATA_RISK_KEYWORDS):
        return True
    if category == TicketCategory.PERFORMANCE_AVAILABILITY and (
        _has_any(text, OUTAGE_KEYWORDS) and _has_any(text, BROAD_IMPACT_KEYWORDS)
    ):
        return True
    if _has_any(text, ("many users blocked", "everyone blocked", "all users blocked")):
        return True
    return False


def _is_vague(text: str, matched_categories: set[TicketCategory]) -> bool:
    if matched_categories:
        return False

    words = re.findall(r"[a-z0-9]+", text)
    if len(words) <= 5:
        return True

    return _has_any(text, GENERIC_VAGUE_PHRASES)


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(_has_term(text, term) for term in terms)


def _has_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _add_reason(reasons: list[ReviewReason], reason: ReviewReason) -> None:
    if reason not in reasons:
        reasons.append(reason)
