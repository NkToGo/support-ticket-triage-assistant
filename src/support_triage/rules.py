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
        "cancel trial",
        "cancel our trial",
        "cancel subscription",
        "cancel plan",
        "cancel renewal",
        "cancellation",
        "payment",
        "payment failed",
        "subscription",
        "renewal",
        "credit",
        "chargeback",
        "expired card",
    ),
    TicketCategory.BUG_REPORT: (
        "alignment",
        "broken",
        "button",
        "cosmetic",
        "error",
        "errors",
        "fails",
        "failed",
        "failure",
        "looks off",
        "pixel",
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
        "whole support team",
        "team is affected",
        "all users",
        "all users affected",
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
        "personal data",
        "gdpr",
        "dpa",
        "suspicious",
        "breach",
        "leak",
        "leaked",
        "exposed",
        "wrong customer",
        "another customer",
        "delete data",
        "data deletion",
        "unauthorized",
        "former employee",
        "former employee access",
        "left the company",
        "disabled account",
    ),
    TicketCategory.FEATURE_REQUEST: (
        "feature request",
        "can you add",
        "please add",
        "improve",
        "suggestion",
        "would be helpful",
        "would like",
        "enhancement",
        "customization",
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
    "whole support team",
    "entire team",
    "team is affected",
    "many users",
    "nobody",
    "company-wide",
    "all users affected",
)
OUTAGE_KEYWORDS = ("outage", "down", "unavailable", "503", "service unavailable")
DATA_RISK_KEYWORDS = (
    "breach",
    "leak",
    "leaked",
    "exposed",
    "data exposure",
    "wrong customer",
    "another customer",
    "data loss",
    "lost data",
)
CROSS_CUSTOMER_DATA_KEYWORDS = ("wrong customer", "another customer")
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
    "dispute",
    "cancel trial",
    "cancel our trial",
    "cancel subscription",
    "cancel plan",
    "cancel renewal",
    "cancellation",
    "credit",
)
ESCALATION_KEYWORDS = (
    "escalation",
    "escalate",
    "legal action",
    "lawsuit",
    "attorney",
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
    "wrong customer",
    "another customer",
    "access to another user",
)
SECURITY_PRIORITY_KEYWORDS = (
    "suspicious",
    "breach",
    "leak",
    "leaked",
    "exposed",
    "delete data",
    "data deletion",
    "gdpr",
    "unauthorized",
    "former employee",
    "left the company",
    "disabled account",
)
LOW_IMPACT_KEYWORDS = (
    "slightly slow",
    "little slow",
    "sometimes",
    "eventually complete",
    "everything still works",
    "no users are blocked",
    "not blocked",
    "no one is blocked",
)
DEGRADED_PERFORMANCE_KEYWORDS = (
    "latency",
    "seconds to load",
    "slow",
)
BUG_LOW_IMPACT_KEYWORDS = (
    "alignment",
    "button",
    "cosmetic",
    "looks off",
    "pixel",
    "everything still works",
)
BUG_HIGH_IMPACT_KEYWORDS = (
    "all projects",
    "multiple projects",
    "finance",
    "using this report today",
    "regression",
    "worked before",
)
INCIDENT_REVIEW_KEYWORDS = OUTAGE_KEYWORDS + ("timeout", "latency")
MISSING_DETAIL_KEYWORDS = (
    "nothing else to add",
    "do not know which details matter",
    "need to gather examples",
    "following up",
    "thing we discussed",
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
    matched_categories = _adjust_category_matches(text, _matched_categories(text))
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
    if vague or category in {TicketCategory.FEATURE_REQUEST, TicketCategory.OTHER_UNCLEAR}:
        return TicketPriority.P3

    if _is_p0(text, category):
        return TicketPriority.P0

    if category == TicketCategory.DATA_SECURITY_PRIVACY:
        if _has_any(text, SECURITY_PRIORITY_KEYWORDS):
            return TicketPriority.P1
        return TicketPriority.P2

    if category == TicketCategory.PERFORMANCE_AVAILABILITY and _has_any(text, LOW_IMPACT_KEYWORDS):
        return TicketPriority.P3
    if category == TicketCategory.PERFORMANCE_AVAILABILITY and (
        _has_any(text, BROAD_IMPACT_KEYWORDS) and _has_any(text, DEGRADED_PERFORMANCE_KEYWORDS)
    ):
        return TicketPriority.P1

    if category == TicketCategory.BUG_REPORT and _has_any(text, BUG_LOW_IMPACT_KEYWORDS):
        return TicketPriority.P3
    if category == TicketCategory.BUG_REPORT and _has_any(text, BUG_HIGH_IMPACT_KEYWORDS):
        return TicketPriority.P1

    if (
        _has_access_blocked_signal(text)
        or _has_any(text, ("blocked core workflow", "cannot work", "blocked from work"))
        or _has_any(text, ESCALATION_KEYWORDS)
    ):
        return TicketPriority.P1

    return TicketPriority.P2


def _choose_routing_target(
    text: str,
    category: TicketCategory,
    priority: TicketPriority,
) -> RoutingTarget:
    if category == TicketCategory.ACCOUNT_ACCESS:
        if _has_access_blocked_signal(text):
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
    if _is_meaningfully_ambiguous(matched_categories):
        _add_reason(reasons, ReviewReason.AMBIGUOUS_CATEGORY)
    if priority in {TicketPriority.P0, TicketPriority.P1}:
        _add_reason(reasons, ReviewReason.PRIORITY_HIGH)
    if category == TicketCategory.DATA_SECURITY_PRIVACY:
        _add_reason(reasons, ReviewReason.SECURITY_OR_PRIVACY)
    if _has_any(text, BILLING_SENSITIVE_KEYWORDS):
        _add_reason(reasons, ReviewReason.BILLING_SENSITIVE)
    if _has_any(text, INCIDENT_REVIEW_KEYWORDS) or (
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
        if _has_access_blocked_signal(text):
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
    if _has_any(text, CROSS_CUSTOMER_DATA_KEYWORDS) and _has_any(text, ("data", "personal data")):
        return True
    if category == TicketCategory.PERFORMANCE_AVAILABILITY and (
        _has_any(text, OUTAGE_KEYWORDS) and _has_any(text, BROAD_IMPACT_KEYWORDS)
    ):
        return True
    if _has_any(text, ("many users blocked", "everyone blocked", "all users blocked")):
        return True
    return False


def _is_vague(text: str, matched_categories: set[TicketCategory]) -> bool:
    if _has_any(text, MISSING_DETAIL_KEYWORDS):
        return True
    if _is_meaningfully_ambiguous(matched_categories) and _has_any(text, ("need to gather examples", "details matter")):
        return True
    if matched_categories:
        return False

    words = re.findall(r"[a-z0-9]+", text)
    if len(words) <= 5:
        return True

    return _has_any(text, GENERIC_VAGUE_PHRASES)


def _adjust_category_matches(
    text: str,
    matched_categories: set[TicketCategory],
) -> set[TicketCategory]:
    adjusted = set(matched_categories)

    if TicketCategory.BILLING_SUBSCRIPTION in adjusted and _has_any(text, ("cancel button", "cancel link")):
        adjusted.discard(TicketCategory.BILLING_SUBSCRIPTION)

    if (
        TicketCategory.BILLING_SUBSCRIPTION in adjusted
        and TicketCategory.BUG_REPORT in adjusted
        and _has_any(text, ("payment failed", "card expired", "expired card"))
    ):
        adjusted.discard(TicketCategory.BUG_REPORT)

    if TicketCategory.DATA_SECURITY_PRIVACY in adjusted:
        adjusted.difference_update(
            {
                TicketCategory.ACCOUNT_ACCESS,
                TicketCategory.BUG_REPORT,
                TicketCategory.TECHNICAL_SUPPORT,
                TicketCategory.PERFORMANCE_AVAILABILITY,
            }
        )

    if (
        TicketCategory.PERFORMANCE_AVAILABILITY in adjusted
        and TicketCategory.ACCOUNT_ACCESS in adjusted
        and _has_any(text, OUTAGE_KEYWORDS)
    ):
        adjusted.discard(TicketCategory.ACCOUNT_ACCESS)

    if (
        TicketCategory.TECHNICAL_SUPPORT in adjusted
        and TicketCategory.ACCOUNT_ACCESS in adjusted
        and _has_any(text, ("saml", "sso", "configure", "setup", "set up", "invite"))
        and not _has_access_blocked_signal(text)
    ):
        adjusted.discard(TicketCategory.ACCOUNT_ACCESS)

    if (
        TicketCategory.BUG_REPORT in adjusted
        and TicketCategory.TECHNICAL_SUPPORT in adjusted
        and _has_any(text, ("error", "fails", "failed", "wrong", "regression", "validation error"))
    ):
        adjusted.discard(TicketCategory.TECHNICAL_SUPPORT)

    if (
        TicketCategory.FEATURE_REQUEST in adjusted
        and _has_any(text, ("feature request", "would be helpful", "would like", "customization", "enhancement"))
        and not _has_any(text, ("error", "fails", "failed", "configure", "configuration"))
    ):
        adjusted = {category for category in adjusted if category != TicketCategory.TECHNICAL_SUPPORT}

    return adjusted


def _is_meaningfully_ambiguous(matched_categories: set[TicketCategory]) -> bool:
    return len(matched_categories) > 1


def _has_access_blocked_signal(text: str) -> bool:
    if _has_any(text, ("no users are blocked", "not blocked", "no one is blocked")):
        return False
    return _has_any(text, ACCESS_BLOCKED_KEYWORDS)


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(_has_term(text, term) for term in terms)


def _has_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _add_reason(reasons: list[ReviewReason], reason: ReviewReason) -> None:
    if reason not in reasons:
        reasons.append(reason)
